from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_permission
from app.inventario import service
from app.inventario.repository import TipoMovimientoRepository
from app.inventario.schemas import (
    MovimientoCrear,
    MovimientoRespuesta,
    ReservaSchema,
    StockRespuesta,
    TipoMovimientoRespuesta,
)

tipo_movimiento_repo = TipoMovimientoRepository()

PERMISO_VER = "inventario.ver"
PERMISO_GESTIONAR = "inventario.gestionar"
ver_requerido = Depends(require_permission(PERMISO_VER))
gestionar_requerido = Depends(require_permission(PERMISO_GESTIONAR))

router = APIRouter(prefix="/api/v1/inventario", tags=["inventario"], dependencies=[ver_requerido])


@router.get("/tipos-movimiento", response_model=list[TipoMovimientoRespuesta])
def listar_tipos_movimiento(db: Session = Depends(get_db)) -> list[TipoMovimientoRespuesta]:
    return list(tipo_movimiento_repo.listar(db))


@router.get("/stock/{variante_id}/{sucursal_id}", response_model=StockRespuesta)
def obtener_stock(variante_id: int, sucursal_id: int, db: Session = Depends(get_db)) -> StockRespuesta:
    return service.obtener_stock(db, variante_id, sucursal_id)


@router.get("/stock", response_model=list[StockRespuesta])
def listar_stock_por_variante(
    variante_id: int = Query(...), db: Session = Depends(get_db)
) -> list[StockRespuesta]:
    return list(service.listar_stock_por_variante(db, variante_id))


@router.get("/kardex", response_model=list[MovimientoRespuesta])
def listar_kardex(
    variante_id: int = Query(...), sucursal_id: int = Query(...), db: Session = Depends(get_db)
) -> list[MovimientoRespuesta]:
    movimientos = service.listar_kardex(db, variante_id, sucursal_id)
    codigos = {tipo.id: tipo.codigo for tipo in tipo_movimiento_repo.listar(db)}
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


routers = [router]
