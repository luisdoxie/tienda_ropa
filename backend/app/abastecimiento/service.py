"""Proveedores, órdenes de compra y recepciones. La recepción es la única
entrada de stock con costo: cada línea llama a
inventario.service.registrar_movimiento(tipo='recepcion') — este paquete
nunca escribe en `stock` ni en `movimiento_inventario` directamente."""

from decimal import Decimal

from sqlalchemy.orm import Session

from app.abastecimiento.models import OrdenCompra, OrdenCompraDetalle, Proveedor, Recepcion, RecepcionDetalle
from app.abastecimiento.repository import (
    OrdenCompraRepository,
    ProductoProveedorRepository,
    ProveedorRepository,
    RecepcionRepository,
)
from app.abastecimiento.schemas import (
    OrdenCompraActualizar,
    OrdenCompraCrear,
    ProveedorCrear,
    RecepcionCrear,
)
from app.catalogo import service as catalogo_service
from app.core.exceptions import ConflictoError, DomainError
from app.inventario import service as inventario_service
from app.organizacion import service as organizacion_service

proveedor_repo = ProveedorRepository()
producto_proveedor_repo = ProductoProveedorRepository()
orden_repo = OrdenCompraRepository()
recepcion_repo = RecepcionRepository()


# ---- Proveedores --------------------------------------------------------------


def agregar_producto_proveedor(
    db: Session, proveedor_id: int, producto_id: int, costo_referencial: Decimal | None, dias_entrega: int | None
):
    proveedor_repo.obtener(db, proveedor_id)  # 404 si no existe / está inactivo
    catalogo_service.obtener_producto(db, producto_id)  # 404 si no existe
    return producto_proveedor_repo.crear(db, proveedor_id, producto_id, costo_referencial, dias_entrega)


def quitar_producto_proveedor(db: Session, proveedor_id: int, producto_id: int) -> None:
    producto_proveedor_repo.eliminar(db, proveedor_id, producto_id)


# ---- Órdenes de compra ----------------------------------------------------------


def crear_orden_compra(db: Session, datos: OrdenCompraCrear, creado_por: int | None) -> OrdenCompra:
    proveedor_repo.obtener(db, datos.proveedor_id)  # 404 si no existe / está inactivo
    organizacion_service.obtener_sucursal(db, datos.sucursal_id)
    for linea in datos.detalle:
        catalogo_service.obtener_variante(db, linea.variante_id)

    if orden_repo.obtener_por_codigo(db, datos.codigo) is not None:
        raise ConflictoError("Ya existe una orden de compra con ese código")

    total = sum((Decimal(linea.cantidad) * linea.costo_unitario for linea in datos.detalle), Decimal("0"))
    orden = OrdenCompra(
        codigo=datos.codigo,
        proveedor_id=datos.proveedor_id,
        sucursal_id=datos.sucursal_id,
        fecha_esperada=datos.fecha_esperada,
        estado="borrador",
        total=total,
        creado_por=creado_por,
    )
    orden.detalle = [
        OrdenCompraDetalle(variante_id=linea.variante_id, cantidad=linea.cantidad, costo_unitario=linea.costo_unitario)
        for linea in datos.detalle
    ]
    return orden_repo.crear(db, orden)


def actualizar_orden_compra(db: Session, orden_id: int, datos: OrdenCompraActualizar) -> OrdenCompra:
    orden = orden_repo.obtener(db, orden_id)
    if orden.estado != "borrador":
        raise ConflictoError("Solo se puede editar una orden de compra en estado 'borrador'")

    if datos.proveedor_id is not None:
        proveedor_repo.obtener(db, datos.proveedor_id)
        orden.proveedor_id = datos.proveedor_id
    if datos.sucursal_id is not None:
        organizacion_service.obtener_sucursal(db, datos.sucursal_id)
        orden.sucursal_id = datos.sucursal_id
    if datos.fecha_esperada is not None:
        orden.fecha_esperada = datos.fecha_esperada

    if datos.detalle is not None:
        for linea in datos.detalle:
            catalogo_service.obtener_variante(db, linea.variante_id)
        nuevas_lineas = [
            OrdenCompraDetalle(variante_id=linea.variante_id, cantidad=linea.cantidad, costo_unitario=linea.costo_unitario)
            for linea in datos.detalle
        ]
        return orden_repo.reemplazar_detalle(db, orden, nuevas_lineas)

    return orden_repo.guardar(db, orden)


def enviar_orden_compra(db: Session, orden_id: int) -> OrdenCompra:
    orden = orden_repo.obtener(db, orden_id)
    if orden.estado != "borrador":
        raise ConflictoError(f"La orden está en estado '{orden.estado}', no se puede enviar")
    orden.estado = "enviada"
    return orden_repo.guardar(db, orden)


def anular_orden_compra(db: Session, orden_id: int) -> OrdenCompra:
    orden = orden_repo.obtener(db, orden_id)
    if orden.estado not in ("borrador", "enviada"):
        raise ConflictoError("Solo se puede anular una orden en 'borrador' o 'enviada'")
    orden.estado = "anulada"
    return orden_repo.guardar(db, orden)


def listar_ordenes_compra(db: Session, proveedor_id: int | None = None, sucursal_id: int | None = None) -> list[OrdenCompra]:
    return orden_repo.listar(db, proveedor_id, sucursal_id)


def obtener_orden_compra(db: Session, orden_id: int) -> OrdenCompra:
    return orden_repo.obtener(db, orden_id)


# ---- Recepciones -------------------------------------------------------------


def _actualizar_estado_orden_por_recepciones(db: Session, orden: OrdenCompra) -> None:
    recibido_por_variante = recepcion_repo.total_recibido_por_variante(db, orden.id)
    completa = all(recibido_por_variante.get(linea.variante_id, 0) >= linea.cantidad for linea in orden.detalle)
    algo_recibido = any(recibido_por_variante.get(linea.variante_id, 0) > 0 for linea in orden.detalle)
    if completa:
        orden.estado = "recibida"
    elif algo_recibido:
        orden.estado = "parcial"


def crear_recepcion(db: Session, datos: RecepcionCrear, empleado_id: int | None, creado_por: int | None) -> Recepcion:
    proveedor_repo.obtener(db, datos.proveedor_id)  # 404 si no existe / está inactivo
    organizacion_service.obtener_sucursal(db, datos.sucursal_id)

    orden = None
    if datos.orden_compra_id is not None:
        orden = orden_repo.obtener(db, datos.orden_compra_id)
        if orden.estado not in ("enviada", "parcial"):
            raise DomainError(f"La orden de compra está en estado '{orden.estado}', no admite recepciones")

    if recepcion_repo.obtener_por_codigo(db, datos.codigo) is not None:
        raise ConflictoError("Ya existe una recepción con ese código")

    recepcion = Recepcion(
        codigo=datos.codigo,
        orden_compra_id=datos.orden_compra_id,
        proveedor_id=datos.proveedor_id,
        sucursal_id=datos.sucursal_id,
        empleado_id=empleado_id,
        observacion=datos.observacion,
    )
    recepcion_repo.crear(db, recepcion)  # flush: recepcion.id ya queda disponible

    for linea in datos.detalle:
        catalogo_service.obtener_variante(db, linea.variante_id)  # 404 si no existe
        db.add(
            RecepcionDetalle(
                recepcion_id=recepcion.id,
                variante_id=linea.variante_id,
                cantidad=linea.cantidad,
                costo_unitario=linea.costo_unitario,
            )
        )
        # commit=False: toda la recepción (cabecera + detalle + los N
        # movimientos que genera) es UNA sola transacción. Si una línea
        # falla (p. ej. tipo de movimiento inválido), no queda nada aplicado.
        inventario_service.registrar_movimiento(
            db,
            variante_id=linea.variante_id,
            sucursal_id=datos.sucursal_id,
            tipo_movimiento_codigo="recepcion",
            cantidad=linea.cantidad,
            costo_unitario=linea.costo_unitario,
            referencia_tipo="recepcion",
            referencia_id=recepcion.id,
            usuario_id=creado_por,
            commit=False,
        )

    db.flush()
    if orden is not None:
        _actualizar_estado_orden_por_recepciones(db, orden)

    db.commit()
    db.refresh(recepcion)
    return recepcion


def listar_recepciones(db: Session, orden_compra_id: int | None = None) -> list[Recepcion]:
    return recepcion_repo.listar(db, orden_compra_id)


def obtener_recepcion(db: Session, recepcion_id: int) -> Recepcion:
    return recepcion_repo.obtener(db, recepcion_id)
