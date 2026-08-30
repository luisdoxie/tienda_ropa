from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import ParametrosPaginacion, parametros_paginacion
from app.core.security import get_current_user, require_permission
from app.ventas import service
from app.ventas.repository import EstadoVentaRepository
from app.ventas.schemas import (
    CarritoDetalleActualizar,
    CarritoDetalleCrear,
    CarritoResumenRespuesta,
    CarritoRespuesta,
    DevolucionCrear,
    DevolucionRespuesta,
    PromocionActualizar,
    PromocionCrear,
    PromocionRespuesta,
    VentaDigitalCrear,
    VentaPresencialCrear,
    VentaRespuesta,
)

estado_repo = EstadoVentaRepository()

PERMISO_DIGITAL = "ventas.digital"
PERMISO_PRESENCIAL = "ventas.presencial"
PERMISO_STAFF = "ventas.gestionar_sucursal"
PERMISO_GESTIONAR = "ventas.gestionar"

digital_requerido = Depends(require_permission(PERMISO_DIGITAL))
presencial_requerido = Depends(require_permission(PERMISO_PRESENCIAL))
staff_requerido = Depends(require_permission(PERMISO_STAFF))
gestionar_requerido = Depends(require_permission(PERMISO_GESTIONAR))


def _venta_respuesta(db: Session, venta) -> VentaRespuesta:
    return VentaRespuesta.from_modelo(venta, estado_repo.mapa_codigos_por_id(db))


# ---- /api/v1/carrito ---------------------------------------------------------------

carrito_router = APIRouter(prefix="/api/v1/carrito", tags=["carrito"], dependencies=[digital_requerido])


@carrito_router.get("", response_model=CarritoRespuesta)
def obtener_mi_carrito(usuario=Depends(get_current_user), db: Session = Depends(get_db)) -> CarritoRespuesta:
    return service.obtener_mi_carrito(db, usuario.id)


@carrito_router.post("", response_model=CarritoRespuesta, status_code=status.HTTP_201_CREATED)
def agregar_al_carrito(
    datos: CarritoDetalleCrear, usuario=Depends(get_current_user), db: Session = Depends(get_db)
) -> CarritoRespuesta:
    return service.agregar_al_carrito(db, usuario.id, datos)


@carrito_router.put("/{variante_id}", response_model=CarritoRespuesta)
def actualizar_linea_carrito(
    variante_id: int,
    datos: CarritoDetalleActualizar,
    usuario=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CarritoRespuesta:
    return service.actualizar_linea_carrito(db, usuario.id, variante_id, datos)


@carrito_router.delete("/{variante_id}", response_model=CarritoRespuesta)
def quitar_del_carrito(
    variante_id: int, usuario=Depends(get_current_user), db: Session = Depends(get_db)
) -> CarritoRespuesta:
    return service.quitar_del_carrito(db, usuario.id, variante_id)


@carrito_router.post("/aplicar-promocion", response_model=CarritoResumenRespuesta)
def aplicar_promocion(usuario=Depends(get_current_user), db: Session = Depends(get_db)) -> CarritoResumenRespuesta:
    return service.previsualizar_carrito(db, usuario.id)


# ---- /api/v1/ventas -----------------------------------------------------------------

ventas_router = APIRouter(prefix="/api/v1/ventas", tags=["ventas"])


@ventas_router.post(
    "/digital", response_model=VentaRespuesta, status_code=status.HTTP_201_CREATED, dependencies=[digital_requerido]
)
def registrar_venta_digital(
    datos: VentaDigitalCrear, usuario=Depends(get_current_user), db: Session = Depends(get_db)
) -> VentaRespuesta:
    venta = service.registrar_venta_digital(db, usuario.id, datos)
    return _venta_respuesta(db, venta)


@ventas_router.post(
    "/presencial",
    response_model=VentaRespuesta,
    status_code=status.HTTP_201_CREATED,
    dependencies=[presencial_requerido],
)
def registrar_venta_presencial(
    datos: VentaPresencialCrear, usuario=Depends(get_current_user), db: Session = Depends(get_db)
) -> VentaRespuesta:
    venta = service.registrar_venta_presencial(db, usuario.id, datos)
    return _venta_respuesta(db, venta)


@ventas_router.get("/mis-compras", response_model=list[VentaRespuesta])
def listar_mis_compras(usuario=Depends(get_current_user), db: Session = Depends(get_db)) -> list[VentaRespuesta]:
    estados = estado_repo.mapa_codigos_por_id(db)
    return [VentaRespuesta.from_modelo(v, estados) for v in service.listar_mis_compras(db, usuario.id)]


@ventas_router.get("/sucursal/{sucursal_id}", response_model=list[VentaRespuesta], dependencies=[staff_requerido])
def listar_ventas_sucursal(sucursal_id: int, db: Session = Depends(get_db)) -> list[VentaRespuesta]:
    estados = estado_repo.mapa_codigos_por_id(db)
    return [VentaRespuesta.from_modelo(v, estados) for v in service.listar_ventas_sucursal(db, sucursal_id)]


@ventas_router.get("/{venta_id}/comprobante", response_model=VentaRespuesta)
def obtener_comprobante(
    venta_id: int, usuario=Depends(get_current_user), db: Session = Depends(get_db)
) -> VentaRespuesta:
    venta = service.obtener_comprobante(db, venta_id, usuario.id)
    return _venta_respuesta(db, venta)


# ---- /api/v1/devoluciones ------------------------------------------------------------

devoluciones_router = APIRouter(prefix="/api/v1/devoluciones", tags=["devoluciones"], dependencies=[staff_requerido])


@devoluciones_router.post("", response_model=DevolucionRespuesta, status_code=status.HTTP_201_CREATED)
def registrar_devolucion(
    datos: DevolucionCrear, usuario=Depends(get_current_user), db: Session = Depends(get_db)
) -> DevolucionRespuesta:
    return service.registrar_devolucion(db, usuario.id, datos)


# ---- /api/v1/promociones -------------------------------------------------------------

promociones_router = APIRouter(prefix="/api/v1/promociones", tags=["promociones"])


@promociones_router.get("", response_model=list[PromocionRespuesta])
def listar_promociones(
    db: Session = Depends(get_db),
    paginacion: ParametrosPaginacion = Depends(parametros_paginacion),
    usuario=Depends(get_current_user),
) -> list[PromocionRespuesta]:
    return service.listar_promociones(db, paginacion)


@promociones_router.get("/{promocion_id}", response_model=PromocionRespuesta)
def obtener_promocion(
    promocion_id: int, db: Session = Depends(get_db), usuario=Depends(get_current_user)
) -> PromocionRespuesta:
    return service.obtener_promocion(db, promocion_id)


@promociones_router.post(
    "", response_model=PromocionRespuesta, status_code=status.HTTP_201_CREATED, dependencies=[gestionar_requerido]
)
def crear_promocion(datos: PromocionCrear, db: Session = Depends(get_db)) -> PromocionRespuesta:
    return service.crear_promocion(db, datos)


@promociones_router.put("/{promocion_id}", response_model=PromocionRespuesta, dependencies=[gestionar_requerido])
def actualizar_promocion(
    promocion_id: int, datos: PromocionActualizar, db: Session = Depends(get_db)
) -> PromocionRespuesta:
    return service.actualizar_promocion(db, promocion_id, datos)


@promociones_router.delete("/{promocion_id}", response_model=PromocionRespuesta, dependencies=[gestionar_requerido])
def desactivar_promocion(promocion_id: int, db: Session = Depends(get_db)) -> PromocionRespuesta:
    return service.desactivar_promocion(db, promocion_id)


routers = [carrito_router, ventas_router, devoluciones_router, promociones_router]
