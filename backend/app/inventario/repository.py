from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NoEncontradoError
from app.inventario.models import MovimientoInventario, Stock, TipoMovimiento


class StockRepository:
    """No hereda de CRUDBase: `stock` no tiene columna `activo` (una fila
    de stock existe o no existe; no se "desactiva") y su creación necesita
    ir bloqueada junto con el resto de `registrar_movimiento`/`reservar_stock`,
    algo que el CRUD genérico no contempla."""

    def obtener_o_crear_bloqueado(self, db: Session, variante_id: int, sucursal_id: int) -> Stock:
        """Devuelve la fila de stock lista para modificar dentro de la
        transacción actual. En Postgres la trae con SELECT FOR UPDATE para
        evitar condiciones de carrera entre movimientos concurrentes sobre
        la misma variante+sucursal; en SQLite (tests) no existe FOR UPDATE,
        así que se omite ahí."""
        consulta = select(Stock).where(Stock.variante_id == variante_id, Stock.sucursal_id == sucursal_id)
        if db.get_bind().dialect.name == "postgresql":
            consulta = consulta.with_for_update()
        stock = db.scalars(consulta).one_or_none()
        if stock is None:
            stock = Stock(
                variante_id=variante_id,
                sucursal_id=sucursal_id,
                cantidad_fisica=0,
                cantidad_reservada=0,
                costo_promedio=Decimal("0"),
            )
            db.add(stock)
            db.flush()
        return stock

    def obtener_por_variante_sucursal(self, db: Session, variante_id: int, sucursal_id: int) -> Stock | None:
        return db.scalar(
            select(Stock).where(Stock.variante_id == variante_id, Stock.sucursal_id == sucursal_id)
        )

    def listar_por_variante(self, db: Session, variante_id: int) -> list[Stock]:
        return list(db.scalars(select(Stock).where(Stock.variante_id == variante_id)))


class MovimientoRepository:
    """Libro inmutable: solo `crear` y consultas de lectura. No hay
    `actualizar` ni `eliminar` a propósito (ver models.MovimientoInventario)."""

    def crear(self, db: Session, movimiento: MovimientoInventario) -> MovimientoInventario:
        db.add(movimiento)
        db.flush()
        return movimiento

    def listar_por_variante_sucursal(
        self, db: Session, variante_id: int, sucursal_id: int
    ) -> list[MovimientoInventario]:
        return list(
            db.scalars(
                select(MovimientoInventario)
                .where(
                    MovimientoInventario.variante_id == variante_id,
                    MovimientoInventario.sucursal_id == sucursal_id,
                )
                .order_by(MovimientoInventario.id)
            )
        )


class TipoMovimientoRepository:
    def obtener_por_codigo(self, db: Session, codigo: str) -> TipoMovimiento:
        tipo = db.scalar(select(TipoMovimiento).where(TipoMovimiento.codigo == codigo))
        if tipo is None:
            raise NoEncontradoError(f"Tipo de movimiento '{codigo}' no encontrado")
        return tipo

    def listar(self, db: Session) -> list[TipoMovimiento]:
        return list(db.scalars(select(TipoMovimiento).order_by(TipoMovimiento.id)))
