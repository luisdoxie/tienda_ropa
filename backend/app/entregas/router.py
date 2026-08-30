from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import ParametrosPaginacion, parametros_paginacion
from app.core.security import get_current_user, require_permission
from app.entregas import service
from app.entregas.repository import EnvioRepository, ZonaEnvioRepository
from app.entregas.schemas import (
    CotizarEnvioRequest,
    CotizarEnvioRespuesta,
    DireccionClienteActualizar,
    DireccionClienteCrear,
    DireccionClienteRespuesta,
    EnvioCrear,
    EnvioEstadoActualizar,
    EnvioRespuesta,
    ZonaEnvioActualizar,
    ZonaEnvioCrear,
    ZonaEnvioRespuesta,
)

zona_repo = ZonaEnvioRepository()
envio_repo = EnvioRepository()

PERMISO_GESTIONAR = "entregas.gestionar"
PERMISO_DIGITAL = "ventas.digital"

gestionar_requerido = Depends(require_permission(PERMISO_GESTIONAR))
digital_requerido = Depends(require_permission(PERMISO_DIGITAL))


# ---- /api/v1/zonas-envio ----------------------------------------------------
# GET es público (el checkout necesita listarlas para elegir); escribir es
# solo de administración/logística.

zonas_router = APIRouter(prefix="/api/v1/zonas-envio", tags=["zonas-envio"])


@zonas_router.get("", response_model=list[ZonaEnvioRespuesta])
def listar_zonas(
    db: Session = Depends(get_db), paginacion: ParametrosPaginacion = Depends(parametros_paginacion)
) -> list[ZonaEnvioRespuesta]:
    return list(zona_repo.listar(db, paginacion))


@zonas_router.get("/{zona_id}", response_model=ZonaEnvioRespuesta)
def obtener_zona(zona_id: int, db: Session = Depends(get_db)) -> ZonaEnvioRespuesta:
    return zona_repo.obtener(db, zona_id)


@zonas_router.post("", response_model=ZonaEnvioRespuesta, status_code=status.HTTP_201_CREATED, dependencies=[gestionar_requerido])
def crear_zona(datos: ZonaEnvioCrear, db: Session = Depends(get_db)) -> ZonaEnvioRespuesta:
    return zona_repo.crear(db, datos)


@zonas_router.put("/{zona_id}", response_model=ZonaEnvioRespuesta, dependencies=[gestionar_requerido])
def actualizar_zona(zona_id: int, datos: ZonaEnvioActualizar, db: Session = Depends(get_db)) -> ZonaEnvioRespuesta:
    return zona_repo.actualizar(db, zona_id, datos)


@zonas_router.delete("/{zona_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[gestionar_requerido])
def desactivar_zona(zona_id: int, db: Session = Depends(get_db)) -> None:
    zona_repo.desactivar(db, zona_id)


# ---- /api/v1/clientes/direcciones ---------------------------------------------
# Recurso propio del cliente logueado: no se listan/editan direcciones de
# otro cliente por id, ver entregas.service._validar_acceso_direccion.

direcciones_router = APIRouter(
    prefix="/api/v1/clientes/direcciones", tags=["direcciones"], dependencies=[digital_requerido]
)


@direcciones_router.get("", response_model=list[DireccionClienteRespuesta])
def listar_mis_direcciones(
    usuario=Depends(get_current_user), db: Session = Depends(get_db)
) -> list[DireccionClienteRespuesta]:
    return service.listar_mis_direcciones(db, usuario.id)


@direcciones_router.post("", response_model=DireccionClienteRespuesta, status_code=status.HTTP_201_CREATED)
def crear_mi_direccion(
    datos: DireccionClienteCrear, usuario=Depends(get_current_user), db: Session = Depends(get_db)
) -> DireccionClienteRespuesta:
    return service.crear_mi_direccion(db, usuario.id, datos)


@direcciones_router.put("/{direccion_id}", response_model=DireccionClienteRespuesta)
def actualizar_mi_direccion(
    direccion_id: int,
    datos: DireccionClienteActualizar,
    usuario=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DireccionClienteRespuesta:
    return service.actualizar_mi_direccion(db, usuario.id, direccion_id, datos)


@direcciones_router.delete("/{direccion_id}", status_code=status.HTTP_204_NO_CONTENT)
def desactivar_mi_direccion(
    direccion_id: int, usuario=Depends(get_current_user), db: Session = Depends(get_db)
) -> None:
    service.desactivar_mi_direccion(db, usuario.id, direccion_id)


# ---- /api/v1/envios ----------------------------------------------------------

envios_router = APIRouter(prefix="/api/v1/envios", tags=["envios"])


@envios_router.post("/cotizar", response_model=CotizarEnvioRespuesta)
def cotizar_envio(datos: CotizarEnvioRequest, db: Session = Depends(get_db)) -> CotizarEnvioRespuesta:
    return service.cotizar_envio(db, datos)


@envios_router.post("", response_model=EnvioRespuesta, status_code=status.HTTP_201_CREATED)
def crear_envio(
    datos: EnvioCrear, usuario=Depends(get_current_user), db: Session = Depends(get_db)
) -> EnvioRespuesta:
    return service.crear_envio(db, usuario.id, datos)


@envios_router.put("/{envio_id}/estado", response_model=EnvioRespuesta, dependencies=[gestionar_requerido])
def actualizar_estado_envio(
    envio_id: int, datos: EnvioEstadoActualizar, db: Session = Depends(get_db)
) -> EnvioRespuesta:
    return service.actualizar_estado_envio(db, envio_id, datos)


routers = [zonas_router, direcciones_router, envios_router]
