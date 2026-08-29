from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_permission
from app.inventario import service
from app.inventario.repository import TipoMovimientoRepository
from app.inventario.schemas import (
    AjusteCrear,
    ConsolidadoRespuesta,
    DisponibilidadRespuesta,
    LimitesActualizar,
    MovimientoCrear,
    MovimientoRespuesta,
    ReservaSchema,
    StockRespuesta,
    TipoMovimientoRespuesta,
    TransferenciaCrear,
    TransferenciaRespuesta,
    ValuacionRespuesta,
)

tipo_movimiento_repo = TipoMovimientoRepository()

PERMISO_VER = "inventario.ver"
PERMISO_GESTIONAR = "inventario.gestionar"
ver_requerido = Depends(require_permission(PERMISO_VER))
gestionar_requerido = Depends(require_permission(PERMISO_GESTIONAR))


def _codigos_tipo_movimiento(db: Session) -> dict[int, str]:
    return {tipo.id: tipo.codigo for tipo in tipo_movimiento_repo.listar(db)}


# ---- /api/v1/inventario/disponibilidad (público) -----------------------------
# Lo consume el catálogo/detalle para mostrar disponibilidad por sucursal.
# Vive separado del resto (sin `ver_requerido`) porque cualquiera lo puede
# consultar, igual que /api/v1/catalogo.

publico_router = APIRouter(prefix="/api/v1/inventario", tags=["inventario"])


@publico_router.get("/disponibilidad", response_model=list[DisponibilidadRespuesta])
def consultar_disponibilidad(
    variante_id: int = Query(...),
    sucursal_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[DisponibilidadRespuesta]:
    return list(service.consultar_disponibilidad(db, variante_id, sucursal_id))


# ---- /api/v1/inventario (administración) --------------------------------------

router = APIRouter(prefix="/api/v1/inventario", tags=["inventario"], dependencies=[ver_requerido])


@router.get("/tipos-movimiento", response_model=list[TipoMovimientoRespuesta])
def listar_tipos_movimiento(db: Session = Depends(get_db)) -> list[TipoMovimientoRespuesta]:
    return list(tipo_movimiento_repo.listar(db))


@router.get("/consolidado", response_model=list[ConsolidadoRespuesta])
def listar_consolidado(
    sucursal_id: int | None = Query(default=None),
    producto_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[ConsolidadoRespuesta]:
    return [ConsolidadoRespuesta(**fila) for fila in service.listar_consolidado(db, sucursal_id, producto_id)]


@router.get("/alertas", response_model=list[ConsolidadoRespuesta])
def listar_alertas(
    sucursal_id: int | None = Query(default=None), db: Session = Depends(get_db)
) -> list[ConsolidadoRespuesta]:
    return [ConsolidadoRespuesta(**fila) for fila in service.listar_alertas(db, sucursal_id)]


@router.get("/valuacion", response_model=list[ValuacionRespuesta])
def listar_valuacion(
    sucursal_id: int | None = Query(default=None), db: Session = Depends(get_db)
) -> list[ValuacionRespuesta]:
    return [ValuacionRespuesta(**fila) for fila in service.listar_valuacion(db, sucursal_id)]


@router.get("/sucursal/{sucursal_id}", response_model=list[StockRespuesta])
def listar_stock_por_sucursal(sucursal_id: int, db: Session = Depends(get_db)) -> list[StockRespuesta]:
    return list(service.listar_stock_por_sucursal(db, sucursal_id))


@router.get("/stock/{variante_id}/{sucursal_id}", response_model=StockRespuesta)
def obtener_stock(variante_id: int, sucursal_id: int, db: Session = Depends(get_db)) -> StockRespuesta:
    return service.obtener_stock(db, variante_id, sucursal_id)


@router.get("/stock", response_model=list[StockRespuesta])
def listar_stock_por_variante(
    variante_id: int = Query(...), db: Session = Depends(get_db)
) -> list[StockRespuesta]:
    return list(service.listar_stock_por_variante(db, variante_id))


@router.put("/stock/{stock_id}/limites", response_model=StockRespuesta, dependencies=[gestionar_requerido])
def actualizar_limites_stock(
    stock_id: int, datos: LimitesActualizar, db: Session = Depends(get_db)
) -> StockRespuesta:
    return service.actualizar_limites_stock(db, stock_id, datos.stock_minimo, datos.stock_maximo)


@router.get("/movimientos", response_model=list[MovimientoRespuesta])
def listar_kardex(
    variante_id: int = Query(...), sucursal_id: int = Query(...), db: Session = Depends(get_db)
) -> list[MovimientoRespuesta]:
    movimientos = service.listar_kardex(db, variante_id, sucursal_id)
    codigos = _codigos_tipo_movimiento(db)
    return [MovimientoRespuesta.from_modelo(m, codigos[m.tipo_movimiento_id]) for m in movimientos]


@router.post(
    "/movimientos",
    response_model=MovimientoRespuesta,
    status_code=status.HTTP_201_CREATED,
    dependencies=[gestionar_requerido],
)
def registrar_movimiento(
    datos: MovimientoCrear, usuario=Depends(get_current_user), db: Session = Depends(get_db)
) -> MovimientoRespuesta:
    movimiento = service.registrar_movimiento(
        db,
        variante_id=datos.variante_id,
        sucursal_id=datos.sucursal_id,
        tipo_movimiento_codigo=datos.tipo_movimiento_codigo,
        cantidad=datos.cantidad,
        costo_unitario=datos.costo_unitario,
        referencia_tipo=datos.referencia_tipo,
        referencia_id=datos.referencia_id,
        usuario_id=usuario.id,
        observacion=datos.observacion,
    )
    tipo = tipo_movimiento_repo.obtener_por_codigo(db, datos.tipo_movimiento_codigo)
    return MovimientoRespuesta.from_modelo(movimiento, tipo.codigo)


@router.post("/reservas", response_model=StockRespuesta, dependencies=[gestionar_requerido])
def reservar_stock(datos: ReservaSchema, db: Session = Depends(get_db)) -> StockRespuesta:
    return service.reservar_stock(db, datos.variante_id, datos.sucursal_id, datos.cantidad)


@router.post("/liberaciones", response_model=StockRespuesta, dependencies=[gestionar_requerido])
def liberar_stock(datos: ReservaSchema, db: Session = Depends(get_db)) -> StockRespuesta:
    return service.liberar_stock(db, datos.variante_id, datos.sucursal_id, datos.cantidad)


@router.post(
    "/ajustes", response_model=MovimientoRespuesta, status_code=status.HTTP_201_CREATED, dependencies=[gestionar_requerido]
)
def registrar_ajuste(
    datos: AjusteCrear, usuario=Depends(get_current_user), db: Session = Depends(get_db)
) -> MovimientoRespuesta:
    movimiento = service.registrar_ajuste(
        db, datos.variante_id, datos.sucursal_id, datos.cantidad, usuario.id, datos.observacion
    )
    codigo = "ajuste_positivo" if datos.cantidad > 0 else "ajuste_negativo"
    return MovimientoRespuesta.from_modelo(movimiento, codigo)


# ---- /api/v1/transferencias ----------------------------------------------------
# Recurso propio (no cuelga de /inventario en la URL) pero vive en este
# paquete: transferencia/transferencia_detalle son tablas de inventario.

transferencias_router = APIRouter(
    prefix="/api/v1/transferencias", tags=["transferencias"], dependencies=[ver_requerido]
)


@transferencias_router.get("", response_model=list[TransferenciaRespuesta])
def listar_transferencias(
    sucursal_id: int | None = Query(default=None), db: Session = Depends(get_db)
) -> list[TransferenciaRespuesta]:
    return list(service.listar_transferencias(db, sucursal_id))


@transferencias_router.get("/{transferencia_id}", response_model=TransferenciaRespuesta)
def obtener_transferencia(transferencia_id: int, db: Session = Depends(get_db)) -> TransferenciaRespuesta:
    return service.obtener_transferencia(db, transferencia_id)


@transferencias_router.post(
    "", response_model=TransferenciaRespuesta, status_code=status.HTTP_201_CREATED, dependencies=[gestionar_requerido]
)
def crear_transferencia(
    datos: TransferenciaCrear, usuario=Depends(get_current_user), db: Session = Depends(get_db)
) -> TransferenciaRespuesta:
    return service.crear_transferencia(db, datos, usuario.id)


@transferencias_router.post(
    "/{transferencia_id}/enviar", response_model=TransferenciaRespuesta, dependencies=[gestionar_requerido]
)
def enviar_transferencia(
    transferencia_id: int, usuario=Depends(get_current_user), db: Session = Depends(get_db)
) -> TransferenciaRespuesta:
    return service.enviar_transferencia(db, transferencia_id, usuario.id)


@transferencias_router.post(
    "/{transferencia_id}/recibir", response_model=TransferenciaRespuesta, dependencies=[gestionar_requerido]
)
def recibir_transferencia(
    transferencia_id: int, usuario=Depends(get_current_user), db: Session = Depends(get_db)
) -> TransferenciaRespuesta:
    return service.recibir_transferencia(db, transferencia_id, usuario.id)


@transferencias_router.delete(
    "/{transferencia_id}", status_code=status.HTTP_200_OK, response_model=TransferenciaRespuesta, dependencies=[gestionar_requerido]
)
def anular_transferencia(transferencia_id: int, db: Session = Depends(get_db)) -> TransferenciaRespuesta:
    return service.anular_transferencia(db, transferencia_id)


routers = [publico_router, router, transferencias_router]
