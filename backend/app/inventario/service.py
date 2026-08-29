"""Corazón del paquete `inventario`: registrar_movimiento() es la regla de
negocio central (kardex + costeo promedio ponderado), y reservar_stock()/
liberar_stock() manejan la cantidad_reservada sin nunca generar un
movimiento ni tocar cantidad_fisica.
"""

from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy.orm import Session

from app.catalogo import service as catalogo_service
from app.core.exceptions import ConflictoError, DomainError, NoEncontradoError
from app.inventario.models import MovimientoInventario, Stock
from app.inventario.repository import MovimientoRepository, StockRepository, TipoMovimientoRepository
from app.organizacion import service as organizacion_service

stock_repo = StockRepository()
movimiento_repo = MovimientoRepository()
tipo_movimiento_repo = TipoMovimientoRepository()

_CUATRO_DECIMALES = Decimal("0.0001")


def registrar_movimiento(
    db: Session,
    *,
    variante_id: int,
    sucursal_id: int,
    tipo_movimiento_codigo: str,
    cantidad: int,
    costo_unitario: Decimal | None = None,
    referencia_tipo: str | None = None,
    referencia_id: int | None = None,
    usuario_id: int | None = None,
    observacion: str | None = None,
) -> MovimientoInventario:
    if cantidad <= 0:
        raise DomainError("cantidad debe ser positiva")

    catalogo_service.obtener_variante(db, variante_id)  # 404 si no existe
    organizacion_service.obtener_sucursal(db, sucursal_id)  # 404 si no existe

    tipo = tipo_movimiento_repo.obtener_por_codigo(db, tipo_movimiento_codigo)

    if tipo.afecta_costo and costo_unitario is None:
        raise DomainError(f"El tipo de movimiento '{tipo.codigo}' requiere costo_unitario")

    # 5. Bloquea la fila de stock (SELECT FOR UPDATE en Postgres) para que
    # dos movimientos concurrentes sobre la misma variante+sucursal no
    # pisen el saldo el uno al otro.
    stock = stock_repo.obtener_o_crear_bloqueado(db, variante_id, sucursal_id)

    cantidad_firmada = cantidad * tipo.signo
    stock_anterior = stock.cantidad_fisica
    nueva_cantidad_fisica = stock_anterior + cantidad_firmada

    if nueva_cantidad_fisica < 0:
        raise ConflictoError("El movimiento dejaría el stock físico en negativo")
    if nueva_cantidad_fisica < stock.cantidad_reservada:
        raise ConflictoError("El movimiento dejaría stock reservado sin respaldo físico")

    # 3. Si el tipo afecta el costo (siempre una entrada: no tiene sentido
    # recalcular el promedio con una salida), recalcula el promedio
    # ponderado con la cantidad y el costo de ESTE ingreso.
    if tipo.afecta_costo and tipo.signo > 0:
        costo_anterior = stock.costo_promedio
        promedio_exacto = (
            Decimal(stock_anterior) * costo_anterior + Decimal(cantidad) * costo_unitario
        ) / Decimal(stock_anterior + cantidad)
        # NUMERIC(12,4) en la base: se redondea acá para que el valor que
        # ve el código sea el mismo que va a quedar persistido.
        nuevo_promedio = promedio_exacto.quantize(_CUATRO_DECIMALES, rounding=ROUND_HALF_UP)
    else:
        nuevo_promedio = stock.costo_promedio

    # 2. y 4. Actualiza stock.cantidad_fisica y costo_promedio.
    stock.cantidad_fisica = nueva_cantidad_fisica
    stock.costo_promedio = nuevo_promedio

    # 1. Inserta el movimiento con su saldo_post y costo_promedio_post.
    movimiento = MovimientoInventario(
        variante_id=variante_id,
        sucursal_id=sucursal_id,
        tipo_movimiento_id=tipo.id,
        cantidad=cantidad_firmada,
        costo_unitario=costo_unitario,
        costo_promedio_post=nuevo_promedio if tipo.afecta_costo else None,
        saldo_post=nueva_cantidad_fisica,
        referencia_tipo=referencia_tipo,
        referencia_id=referencia_id,
        usuario_id=usuario_id,
        observacion=observacion,
    )
    movimiento_repo.crear(db, movimiento)

    db.commit()
    db.refresh(movimiento)
    return movimiento


def reservar_stock(db: Session, variante_id: int, sucursal_id: int, cantidad: int) -> Stock:
    """Incrementa cantidad_reservada. Nunca toca cantidad_fisica ni genera
    movimiento de inventario."""
    if cantidad <= 0:
        raise DomainError("cantidad debe ser positiva")

    catalogo_service.obtener_variante(db, variante_id)
    organizacion_service.obtener_sucursal(db, sucursal_id)

    stock = stock_repo.obtener_o_crear_bloqueado(db, variante_id, sucursal_id)
    disponible = stock.cantidad_fisica - stock.cantidad_reservada
    if cantidad > disponible:
        raise ConflictoError("No hay stock disponible suficiente para reservar")

    stock.cantidad_reservada += cantidad
    db.commit()
    db.refresh(stock)
    return stock


def liberar_stock(db: Session, variante_id: int, sucursal_id: int, cantidad: int) -> Stock:
    """Decrementa cantidad_reservada. Nunca toca cantidad_fisica ni genera
    movimiento de inventario."""
    if cantidad <= 0:
        raise DomainError("cantidad debe ser positiva")

    stock = stock_repo.obtener_o_crear_bloqueado(db, variante_id, sucursal_id)
    if cantidad > stock.cantidad_reservada:
        raise ConflictoError("No se puede liberar más de lo reservado")

    stock.cantidad_reservada -= cantidad
    db.commit()
    db.refresh(stock)
    return stock


def obtener_stock(db: Session, variante_id: int, sucursal_id: int) -> Stock:
    stock = stock_repo.obtener_por_variante_sucursal(db, variante_id, sucursal_id)
    if stock is None:
        raise NoEncontradoError("Todavía no hay stock registrado para esa variante en esa sucursal")
    return stock


def listar_stock_por_variante(db: Session, variante_id: int) -> list[Stock]:
    catalogo_service.obtener_variante(db, variante_id)
    return stock_repo.listar_por_variante(db, variante_id)


def listar_kardex(db: Session, variante_id: int, sucursal_id: int) -> list[MovimientoInventario]:
    catalogo_service.obtener_variante(db, variante_id)
    organizacion_service.obtener_sucursal(db, sucursal_id)
    return movimiento_repo.listar_por_variante_sucursal(db, variante_id, sucursal_id)
