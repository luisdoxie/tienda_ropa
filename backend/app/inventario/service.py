"""Corazón del paquete `inventario`: registrar_movimiento() es la regla de
negocio central (kardex + costeo promedio ponderado), y reservar_stock()/
liberar_stock() manejan la cantidad_reservada sin nunca generar un
movimiento ni tocar cantidad_fisica.
"""

import datetime as dt
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy.orm import Session

from app.catalogo import service as catalogo_service
from app.core.exceptions import ConflictoError, DomainError, NoEncontradoError
from app.inventario import repository as inventario_repo
from app.inventario.models import MovimientoInventario, Stock, Transferencia, TransferenciaDetalle
from app.inventario.repository import (
    MovimientoRepository,
    StockRepository,
    TipoMovimientoRepository,
    TransferenciaRepository,
)
from app.inventario.schemas import TransferenciaCrear
from app.organizacion import service as organizacion_service

stock_repo = StockRepository()
movimiento_repo = MovimientoRepository()
tipo_movimiento_repo = TipoMovimientoRepository()
transferencia_repo = TransferenciaRepository()

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
    commit: bool = True,
) -> MovimientoInventario:
    """`commit=False` lo usan operaciones de otros paquetes que registran
    varios movimientos como una sola transacción (p. ej.
    abastecimiento.crear_recepcion con varias líneas, o
    enviar_transferencia/recibir_transferencia acá mismo): si una línea
    falla, ninguna de las anteriores debe quedar aplicada. Quien pasa
    `commit=False` es responsable de hacer `db.commit()` al final."""
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

    if commit:
        db.commit()
    else:
        db.flush()
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


def listar_stock_por_sucursal(db: Session, sucursal_id: int) -> list[Stock]:
    organizacion_service.obtener_sucursal(db, sucursal_id)  # 404 si no existe
    return stock_repo.listar_por_sucursal(db, sucursal_id)


def consultar_disponibilidad(db: Session, variante_id: int, sucursal_id: int | None = None) -> list[Stock]:
    """Público: lo consume el catálogo/detalle para mostrar disponibilidad
    por sucursal. Sin stock registrado en una sucursal no es un error, es
    simplemente 0 unidades ahí (no se levanta 404)."""
    catalogo_service.obtener_variante(db, variante_id)  # 404 si no existe
    stocks = stock_repo.listar_por_variante(db, variante_id)
    if sucursal_id is not None:
        stocks = [s for s in stocks if s.sucursal_id == sucursal_id]
    return stocks


def actualizar_limites_stock(
    db: Session, stock_id: int, stock_minimo: int | None, stock_maximo: int | None
) -> Stock:
    stock = stock_repo.obtener(db, stock_id)
    minimo_final = stock_minimo if stock_minimo is not None else stock.stock_minimo
    maximo_final = stock_maximo if stock_maximo is not None else stock.stock_maximo
    if maximo_final is not None and maximo_final < minimo_final:
        raise DomainError("stock_maximo no puede ser menor que stock_minimo")
    return stock_repo.actualizar_limites(db, stock, stock_minimo, stock_maximo)


def listar_consolidado(db: Session, sucursal_id: int | None = None, producto_id: int | None = None) -> list[dict]:
    return inventario_repo.consolidado(db, sucursal_id, producto_id)


def listar_alertas(db: Session, sucursal_id: int | None = None) -> list[dict]:
    return inventario_repo.alertas(db, sucursal_id)


def listar_valuacion(db: Session, sucursal_id: int | None = None) -> list[dict]:
    return inventario_repo.valuacion(db, sucursal_id)


# ---- Ajustes ------------------------------------------------------------------


def registrar_ajuste(
    db: Session, variante_id: int, sucursal_id: int, cantidad: int, usuario_id: int | None, observacion: str | None
) -> MovimientoInventario:
    """Envoltorio delgado sobre registrar_movimiento(): traduce el signo de
    `cantidad` (positivo = sobrante, negativo = faltante) al tipo de
    movimiento correspondiente."""
    if cantidad == 0:
        raise DomainError("cantidad no puede ser cero")
    tipo_codigo = "ajuste_positivo" if cantidad > 0 else "ajuste_negativo"
    return registrar_movimiento(
        db,
        variante_id=variante_id,
        sucursal_id=sucursal_id,
        tipo_movimiento_codigo=tipo_codigo,
        cantidad=abs(cantidad),
        referencia_tipo="ajuste",
        usuario_id=usuario_id,
        observacion=observacion,
    )


# ---- Transferencias -----------------------------------------------------------


def crear_transferencia(db: Session, datos: TransferenciaCrear, usuario_id: int | None) -> Transferencia:
    if datos.sucursal_origen_id == datos.sucursal_destino_id:
        raise DomainError("La sucursal de origen y destino no pueden ser la misma")
    organizacion_service.obtener_sucursal(db, datos.sucursal_origen_id)
    organizacion_service.obtener_sucursal(db, datos.sucursal_destino_id)
    for linea in datos.detalle:
        catalogo_service.obtener_variante(db, linea.variante_id)

    if transferencia_repo.obtener_por_codigo(db, datos.codigo) is not None:
        raise ConflictoError("Ya existe una transferencia con ese código")

    transferencia = Transferencia(
        codigo=datos.codigo,
        sucursal_origen_id=datos.sucursal_origen_id,
        sucursal_destino_id=datos.sucursal_destino_id,
        estado="pendiente",
        usuario_id=usuario_id,
    )
    transferencia.detalle = [
        TransferenciaDetalle(variante_id=linea.variante_id, cantidad=linea.cantidad) for linea in datos.detalle
    ]
    return transferencia_repo.crear(db, transferencia)


def listar_transferencias(db: Session, sucursal_id: int | None = None) -> list[Transferencia]:
    return transferencia_repo.listar(db, sucursal_id)


def obtener_transferencia(db: Session, transferencia_id: int) -> Transferencia:
    return transferencia_repo.obtener(db, transferencia_id)


def enviar_transferencia(db: Session, transferencia_id: int, usuario_id: int | None) -> Transferencia:
    """Genera la salida en la sucursal de origen: un movimiento
    `transferencia_out` por línea, todo en una sola transacción (si una
    línea no tiene stock suficiente, ninguna queda aplicada)."""
    transferencia = transferencia_repo.obtener(db, transferencia_id)
    if transferencia.estado != "pendiente":
        raise ConflictoError(f"La transferencia está en estado '{transferencia.estado}', no se puede enviar")

    for linea in transferencia.detalle:
        registrar_movimiento(
            db,
            variante_id=linea.variante_id,
            sucursal_id=transferencia.sucursal_origen_id,
            tipo_movimiento_codigo="transferencia_out",
            cantidad=linea.cantidad,
            referencia_tipo="transferencia",
            referencia_id=transferencia.id,
            usuario_id=usuario_id,
            commit=False,
        )

    transferencia.estado = "en_transito"
    transferencia.fecha_envio = dt.datetime.now(dt.timezone.utc)
    db.commit()
    db.refresh(transferencia)
    return transferencia


def recibir_transferencia(db: Session, transferencia_id: int, usuario_id: int | None) -> Transferencia:
    """Genera el ingreso en la sucursal de destino usando el costo
    promedio ACTUAL del origen (transferencia_out no lo modifica, así que
    es el mismo costo que tenía la mercadería al salir)."""
    transferencia = transferencia_repo.obtener(db, transferencia_id)
    if transferencia.estado != "en_transito":
        raise ConflictoError(f"La transferencia está en estado '{transferencia.estado}', no se puede recibir")

    for linea in transferencia.detalle:
        stock_origen = stock_repo.obtener_por_variante_sucursal(
            db, linea.variante_id, transferencia.sucursal_origen_id
        )
        costo_origen = stock_origen.costo_promedio if stock_origen is not None else Decimal("0")
        registrar_movimiento(
            db,
            variante_id=linea.variante_id,
            sucursal_id=transferencia.sucursal_destino_id,
            tipo_movimiento_codigo="transferencia_in",
            cantidad=linea.cantidad,
            costo_unitario=costo_origen,
            referencia_tipo="transferencia",
            referencia_id=transferencia.id,
            usuario_id=usuario_id,
            commit=False,
        )

    transferencia.estado = "recibida"
    transferencia.fecha_recepcion = dt.datetime.now(dt.timezone.utc)
    db.commit()
    db.refresh(transferencia)
    return transferencia


def anular_transferencia(db: Session, transferencia_id: int) -> Transferencia:
    transferencia = transferencia_repo.obtener(db, transferencia_id)
    if transferencia.estado != "pendiente":
        raise ConflictoError("Solo se puede anular una transferencia pendiente (todavía sin movimientos)")
    transferencia.estado = "anulada"
    db.commit()
    db.refresh(transferencia)
    return transferencia
