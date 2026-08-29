from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_permission, require_service_token
from app.reservas import service
from app.reservas.repository import EstadoReservaRepository
from app.reservas.schemas import ReservaCrear, ReservaRespuesta, SeleccionActualizar

estado_repo = EstadoReservaRepository()

PERMISO_CREAR = "reservas.crear"
PERMISO_STAFF = "reservas.gestionar_sucursal"
crear_requerido = Depends(require_permission(PERMISO_CREAR))
staff_requerido = Depends(require_permission(PERMISO_STAFF))


def _respuesta(db: Session, reserva) -> ReservaRespuesta:
    return ReservaRespuesta.from_modelo(reserva, estado_repo.mapa_codigos_por_id(db))


router = APIRouter(prefix="/api/v1/reservas", tags=["reservas"])


@router.post("", response_model=ReservaRespuesta, status_code=status.HTTP_201_CREATED, dependencies=[crear_requerido])
def crear_reserva(
    datos: ReservaCrear, usuario=Depends(get_current_user), db: Session = Depends(get_db)
) -> ReservaRespuesta:
    reserva = service.crear_reserva(db, usuario.id, datos)
    return _respuesta(db, reserva)


@router.get("/mis-reservas", response_model=list[ReservaRespuesta], dependencies=[crear_requerido])
def listar_mis_reservas(usuario=Depends(get_current_user), db: Session = Depends(get_db)) -> list[ReservaRespuesta]:
    estados = estado_repo.mapa_codigos_por_id(db)
    return [ReservaRespuesta.from_modelo(r, estados) for r in service.listar_mis_reservas(db, usuario.id)]


@router.get("/sucursal/{sucursal_id}", response_model=list[ReservaRespuesta], dependencies=[staff_requerido])
def listar_reservas_sucursal(sucursal_id: int, db: Session = Depends(get_db)) -> list[ReservaRespuesta]:
    estados = estado_repo.mapa_codigos_por_id(db)
    return [ReservaRespuesta.from_modelo(r, estados) for r in service.listar_reservas_sucursal(db, sucursal_id)]


@router.get("/{reserva_id}", response_model=ReservaRespuesta)
def obtener_reserva(
    reserva_id: int, usuario=Depends(get_current_user), db: Session = Depends(get_db)
) -> ReservaRespuesta:
    reserva = service.obtener_reserva(db, reserva_id, usuario.id)
    return _respuesta(db, reserva)


@router.delete("/{reserva_id}", response_model=ReservaRespuesta)
def cancelar_reserva(
    reserva_id: int, usuario=Depends(get_current_user), db: Session = Depends(get_db)
) -> ReservaRespuesta:
    reserva = service.cancelar_reserva(db, reserva_id, usuario.id)
    return _respuesta(db, reserva)


@router.put("/{reserva_id}/preparar", response_model=ReservaRespuesta, dependencies=[staff_requerido])
def preparar_reserva(
    reserva_id: int, usuario=Depends(get_current_user), db: Session = Depends(get_db)
) -> ReservaRespuesta:
    reserva = service.preparar_reserva(db, reserva_id, usuario.id)
    return _respuesta(db, reserva)


@router.put("/{reserva_id}/confirmar-llegada", response_model=ReservaRespuesta, dependencies=[staff_requerido])
def confirmar_llegada(
    reserva_id: int, usuario=Depends(get_current_user), db: Session = Depends(get_db)
) -> ReservaRespuesta:
    reserva = service.confirmar_llegada(db, reserva_id, usuario.id)
    return _respuesta(db, reserva)


@router.put("/{reserva_id}/seleccion", response_model=ReservaRespuesta, dependencies=[staff_requerido])
def registrar_seleccion(
    reserva_id: int, datos: SeleccionActualizar, usuario=Depends(get_current_user), db: Session = Depends(get_db)
) -> ReservaRespuesta:
    reserva = service.registrar_seleccion(db, reserva_id, usuario.id, datos)
    return _respuesta(db, reserva)


# ---- /api/v1/tareas ---------------------------------------------------------------
# Protegida por token de servicio (no por JWT): la dispara un cron/scheduler,
# no una persona logueada.

tareas_router = APIRouter(prefix="/api/v1/tareas", tags=["tareas"], dependencies=[Depends(require_service_token)])


@tareas_router.post("/expirar-reservas")
def expirar_reservas(db: Session = Depends(get_db)) -> dict:
    cantidad = service.expirar_reservas(db)
    return {"expiradas": cantidad}


routers = [router, tareas_router]
