"""Ventas: registrar_venta_presencial()/registrar_venta_digital() son la
regla de negocio central, delegada en `_registrar_venta()`, que hace TODO
en una sola transacción (una línea sin stock revierte la venta entera):

1. Valida disponibilidad de cada línea (vía inventario.service, antes de
   tocar nada).
2. Crea venta y venta_detalle, congelando `costo_unitario` desde
   `stock.costo_promedio` de ese momento -- nunca se recalcula después,
   aunque cambie el costo promedio real de la variante (ver el docstring
   de VentaDetalle.costo_unitario y los tests de "Revisar").
3. Llama a inventario.service.registrar_movimiento() tipo 'venta' por
   cada línea.
4. Si la venta viene de una reserva, libera el stock reservado de esa
   línea antes del movimiento (si no, registrar_movimiento rechazaría
   dejar cantidad_reservada sin respaldo físico) y usa las líneas que el
   cliente ya marcó `seleccionada=True` al probarse (reservas.service ya
   deja la reserva en 'completada' en ese momento; acá no hay una
   transición aparte, solo se valida que ya haya pasado).
5. Aplica promociones vigentes según `promocion_alcance`: si más de una
   promoción matchea la misma línea, se toma la de mayor descuento (el
   enunciado no dice si se acumulan, y acumular sin límite podría dejar
   precios negativos).
6. Calcula subtotal (bruto, antes de descuento), descuento, costo de
   envío y total.
"""

from __future__ import annotations

import datetime as dt
import secrets
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.catalogo import service as catalogo_service
from app.catalogo.models import ProductoVariante
from app.core.deps import ParametrosPaginacion
from app.core.exceptions import ConflictoError, DomainError, NoEncontradoError, PermisoDenegadoError
from app.core.security import permisos_de_usuario
from app.inventario import service as inventario_service
from app.organizacion import service as organizacion_service
from app.reservas import service as reservas_service
from app.seguridad import service as seguridad_service
from app.ventas.models import (
    Carrito,
    CarritoDetalle,
    Devolucion,
    DevolucionDetalle,
    Promocion,
    PromocionAlcance,
    Venta,
    VentaDetalle,
)
from app.ventas.repository import (
    CarritoRepository,
    DevolucionRepository,
    EstadoVentaRepository,
    PromocionRepository,
    VentaRepository,
)
from app.ventas.schemas import (
    CarritoDetalleActualizar,
    CarritoDetalleCrear,
    CarritoDetalleRespuesta,
    CarritoResumenLinea,
    CarritoResumenRespuesta,
    CarritoRespuesta,
    DevolucionCrear,
    PromocionActualizar,
    PromocionAlcanceCrear,
    PromocionCrear,
    VentaDigitalCrear,
    VentaPresencialCrear,
)

estado_repo = EstadoVentaRepository()
venta_repo = VentaRepository()
promocion_repo = PromocionRepository()
carrito_repo = CarritoRepository()
devolucion_repo = DevolucionRepository()

PERMISO_STAFF = "ventas.gestionar_sucursal"

_DOS_DECIMALES = Decimal("0.01")


def _redondear(valor: Decimal) -> Decimal:
    return valor.quantize(_DOS_DECIMALES, rounding=ROUND_HALF_UP)


def _generar_codigo(db: Session, prefijo: str, existe_codigo) -> str:
    for _ in range(5):
        codigo = f"{prefijo}-{secrets.token_hex(4).upper()}"
        if existe_codigo(db, codigo) is None:
            return codigo
    raise DomainError("No se pudo generar un código único, reintentá")


def _es_staff(db: Session, usuario_id: int) -> bool:
    return PERMISO_STAFF in permisos_de_usuario(db, usuario_id)


# ---- Cálculo de precio + promoción ------------------------------------------------


def _calcular_linea(db: Session, variante: ProductoVariante, cantidad: int, hoy: dt.date) -> tuple[Decimal, Decimal, Decimal]:
    """(precio_unitario, descuento_unitario, subtotal_neto) de una línea."""
    precio_unitario = catalogo_service.obtener_precio_efectivo(variante)
    producto_id, categoria_id, temporada_id = catalogo_service.obtener_info_promocion(variante)
    promociones = promocion_repo.listar_vigentes_para(
        db, producto_id=producto_id, categoria_id=categoria_id, temporada_id=temporada_id, hoy=hoy
    )

    descuento_unitario = Decimal("0")
    for promocion in promociones:
        if promocion.tipo == "porcentaje":
            candidato = precio_unitario * promocion.valor / Decimal("100")
        else:
            candidato = promocion.valor
        candidato = min(candidato, precio_unitario)  # nunca deja el precio negativo
        descuento_unitario = max(descuento_unitario, candidato)

    descuento_unitario = _redondear(descuento_unitario)
    subtotal = _redondear((precio_unitario - descuento_unitario) * cantidad)
    return precio_unitario, descuento_unitario, subtotal


# ---- Venta: regla central ----------------------------------------------------------


def _registrar_venta(
    db: Session,
    *,
    canal: str,
    sucursal_id: int,
    lineas: list[tuple[int, int]],
    cliente_id: int | None,
    cajero_id: int | None,
    reserva_id: int | None,
    costo_envio: Decimal,
    usuario_id: int | None,
    carrito_a_vaciar: Carrito | None = None,
) -> Venta:
    if not lineas:
        raise DomainError("La venta necesita al menos una línea")

    organizacion_service.obtener_sucursal(db, sucursal_id)
    hoy = dt.date.today()

    # 1. Valida disponibilidad de TODAS las líneas antes de tocar nada.
    variantes: dict[int, ProductoVariante] = {}
    for variante_id, cantidad in lineas:
        variante = catalogo_service.obtener_variante(db, variante_id)  # 404 si no existe
        variantes[variante_id] = variante
        disponibilidad = inventario_service.consultar_disponibilidad(db, variante_id, sucursal_id)
        disponible = sum(s.cantidad_disponible for s in disponibilidad)
        if cantidad > disponible:
            raise ConflictoError(f"No hay stock disponible suficiente de la variante {variante_id}")

    estado_inicial = estado_repo.obtener_por_codigo(db, "pendiente_pago")
    venta = Venta(
        codigo=_generar_codigo(db, "VTA", venta_repo.obtener_por_codigo),
        canal=canal,
        cliente_id=cliente_id,
        sucursal_id=sucursal_id,
        cajero_id=cajero_id,
        reserva_id=reserva_id,
        estado_id=estado_inicial.id,
        costo_envio=costo_envio,
    )
    venta_repo.crear(db, venta)  # flush: venta.id ya disponible

    subtotal_bruto = Decimal("0")
    descuento_total = Decimal("0")

    for variante_id, cantidad in lineas:
        variante = variantes[variante_id]

        # 2. Congela el costo ANTES del movimiento de inventario.
        stock_actual = inventario_service.obtener_stock(db, variante_id, sucursal_id)
        costo_unitario = stock_actual.costo_promedio

        precio_unitario, descuento_unitario, subtotal_linea = _calcular_linea(db, variante, cantidad, hoy)

        db.add(
            VentaDetalle(
                venta_id=venta.id,
                variante_id=variante_id,
                cantidad=cantidad,
                precio_unitario=precio_unitario,
                descuento_unitario=descuento_unitario,
                costo_unitario=costo_unitario,
                subtotal=subtotal_linea,
            )
        )
        subtotal_bruto += precio_unitario * cantidad
        descuento_total += descuento_unitario * cantidad

        # 4. Libera lo reservado (si aplica) antes de descontar físicamente.
        if reserva_id is not None:
            inventario_service.liberar_stock(db, variante_id, sucursal_id, cantidad, commit=False)

        # 3. Movimiento de inventario tipo 'venta'.
        inventario_service.registrar_movimiento(
            db,
            variante_id=variante_id,
            sucursal_id=sucursal_id,
            tipo_movimiento_codigo="venta",
            cantidad=cantidad,
            referencia_tipo="venta",
            referencia_id=venta.id,
            usuario_id=usuario_id,
            commit=False,
        )

    # 6. Totales.
    venta.subtotal = _redondear(subtotal_bruto)
    venta.descuento = _redondear(descuento_total)
    venta.total = _redondear(venta.subtotal - venta.descuento + venta.costo_envio)

    if carrito_a_vaciar is not None:
        carrito_repo.vaciar(db, carrito_a_vaciar)

    db.commit()
    db.refresh(venta)
    return venta


def registrar_venta_presencial(db: Session, usuario_id: int, datos: VentaPresencialCrear) -> Venta:
    empleado = organizacion_service.obtener_empleado_por_usuario(db, usuario_id)
    if empleado is None:
        raise PermisoDenegadoError("Este usuario no es un empleado, no puede registrar ventas presenciales")

    if datos.reserva_id is not None:
        reserva = reservas_service.obtener_reserva_para_venta(db, datos.reserva_id)
        lineas = [(linea.variante_id, linea.cantidad) for linea in reserva.detalle if linea.seleccionada]
        if not lineas:
            raise DomainError("La reserva no tiene ninguna línea seleccionada para comprar")
        cliente_id = reserva.cliente_id
    else:
        if not datos.detalle:
            raise DomainError("La venta necesita al menos una línea (o un reserva_id)")
        lineas = [(linea.variante_id, linea.cantidad) for linea in datos.detalle]
        cliente_id = datos.cliente_id
        if cliente_id is not None:
            seguridad_service.obtener_cliente(db, cliente_id)  # 404 si no existe

    return _registrar_venta(
        db,
        canal="presencial",
        sucursal_id=datos.sucursal_id,
        lineas=lineas,
        cliente_id=cliente_id,
        cajero_id=empleado.id,
        reserva_id=datos.reserva_id,
        costo_envio=Decimal("0"),
        usuario_id=usuario_id,
    )


def registrar_venta_digital(db: Session, usuario_id: int, datos: VentaDigitalCrear) -> Venta:
    cliente = seguridad_service.obtener_perfil_cliente(db, usuario_id)
    carrito = carrito_repo.obtener_por_cliente(db, cliente.id)
    if carrito is None or not carrito.detalle:
        raise DomainError("El carrito está vacío")

    lineas = [(linea.variante_id, linea.cantidad) for linea in carrito.detalle]

    return _registrar_venta(
        db,
        canal="digital",
        sucursal_id=datos.sucursal_id,
        lineas=lineas,
        cliente_id=cliente.id,
        cajero_id=None,
        reserva_id=None,
        costo_envio=datos.costo_envio,
        usuario_id=usuario_id,
        carrito_a_vaciar=carrito,
    )


# ---- Consultas de ventas ------------------------------------------------------------


def _validar_acceso_venta(db: Session, venta: Venta, usuario_id: int) -> None:
    if _es_staff(db, usuario_id):
        return
    cliente = seguridad_service.obtener_perfil_cliente(db, usuario_id)
    if cliente is None or venta.cliente_id != cliente.id:
        raise PermisoDenegadoError("No tenés acceso a esta venta")


def obtener_comprobante(db: Session, venta_id: int, usuario_id: int) -> Venta:
    venta = venta_repo.obtener(db, venta_id)
    _validar_acceso_venta(db, venta, usuario_id)
    return venta


def listar_mis_compras(db: Session, usuario_id: int) -> list[Venta]:
    cliente = seguridad_service.obtener_perfil_cliente(db, usuario_id)
    return venta_repo.listar_por_cliente(db, cliente.id)


def listar_ventas_sucursal(db: Session, sucursal_id: int) -> list[Venta]:
    organizacion_service.obtener_sucursal(db, sucursal_id)
    return venta_repo.listar_por_sucursal(db, sucursal_id)


# ---- Carrito --------------------------------------------------------------------


def _carrito_respuesta(db: Session, carrito: Carrito) -> CarritoRespuesta:
    detalle_resp = []
    subtotal = Decimal("0")
    for linea in carrito.detalle:
        variante = catalogo_service.obtener_variante(db, linea.variante_id)
        precio_unitario = catalogo_service.obtener_precio_efectivo(variante)
        subtotal_linea = _redondear(precio_unitario * linea.cantidad)
        detalle_resp.append(
            CarritoDetalleRespuesta(
                id=linea.id,
                variante_id=linea.variante_id,
                cantidad=linea.cantidad,
                precio_unitario=precio_unitario,
                subtotal=subtotal_linea,
            )
        )
        subtotal += subtotal_linea

    return CarritoRespuesta(
        id=carrito.id,
        cliente_id=carrito.cliente_id,
        sucursal_id=carrito.sucursal_id,
        actualizado_en=carrito.actualizado_en,
        detalle=detalle_resp,
        subtotal=_redondear(subtotal),
    )


def obtener_mi_carrito(db: Session, usuario_id: int) -> CarritoRespuesta:
    cliente = seguridad_service.obtener_perfil_cliente(db, usuario_id)
    carrito = carrito_repo.obtener_o_crear(db, cliente.id)
    db.commit()  # persiste el carrito si obtener_o_crear tuvo que crearlo
    return _carrito_respuesta(db, carrito)


def agregar_al_carrito(db: Session, usuario_id: int, datos: CarritoDetalleCrear) -> CarritoRespuesta:
    cliente = seguridad_service.obtener_perfil_cliente(db, usuario_id)
    catalogo_service.obtener_variante(db, datos.variante_id)  # 404 si no existe
    carrito = carrito_repo.obtener_o_crear(db, cliente.id)

    linea = carrito_repo.obtener_linea(db, carrito.id, datos.variante_id)
    if linea is None:
        db.add(CarritoDetalle(carrito_id=carrito.id, variante_id=datos.variante_id, cantidad=datos.cantidad))
    else:
        linea.cantidad += datos.cantidad

    db.commit()
    db.refresh(carrito)
    return _carrito_respuesta(db, carrito)


def actualizar_linea_carrito(
    db: Session, usuario_id: int, variante_id: int, datos: CarritoDetalleActualizar
) -> CarritoRespuesta:
    cliente = seguridad_service.obtener_perfil_cliente(db, usuario_id)
    carrito = carrito_repo.obtener_o_crear(db, cliente.id)
    linea = carrito_repo.obtener_linea(db, carrito.id, variante_id)
    if linea is None:
        raise NoEncontradoError("Esa variante no está en el carrito")

    linea.cantidad = datos.cantidad
    db.commit()
    db.refresh(carrito)
    return _carrito_respuesta(db, carrito)


def quitar_del_carrito(db: Session, usuario_id: int, variante_id: int) -> CarritoRespuesta:
    cliente = seguridad_service.obtener_perfil_cliente(db, usuario_id)
    carrito = carrito_repo.obtener_o_crear(db, cliente.id)
    linea = carrito_repo.obtener_linea(db, carrito.id, variante_id)
    if linea is None:
        raise NoEncontradoError("Esa variante no está en el carrito")

    db.delete(linea)
    db.commit()
    db.refresh(carrito)
    return _carrito_respuesta(db, carrito)


def previsualizar_carrito(db: Session, usuario_id: int) -> CarritoResumenRespuesta:
    """POST /carrito/aplicar-promocion: no hay código de cupón que canjear
    (`promocion` no tiene esa columna) -- esto recalcula el carrito con las
    promociones vigentes ya aplicadas solas, según `promocion_alcance`."""
    cliente = seguridad_service.obtener_perfil_cliente(db, usuario_id)
    carrito = carrito_repo.obtener_o_crear(db, cliente.id)
    db.commit()
    hoy = dt.date.today()

    lineas: list[CarritoResumenLinea] = []
    subtotal = Decimal("0")
    descuento = Decimal("0")
    for linea in carrito.detalle:
        variante = catalogo_service.obtener_variante(db, linea.variante_id)
        precio_unitario, descuento_unitario, subtotal_linea = _calcular_linea(db, variante, linea.cantidad, hoy)
        lineas.append(
            CarritoResumenLinea(
                variante_id=linea.variante_id,
                cantidad=linea.cantidad,
                precio_unitario=precio_unitario,
                descuento_unitario=descuento_unitario,
                subtotal=subtotal_linea,
            )
        )
        subtotal += precio_unitario * linea.cantidad
        descuento += descuento_unitario * linea.cantidad

    subtotal = _redondear(subtotal)
    descuento = _redondear(descuento)
    return CarritoResumenRespuesta(lineas=lineas, subtotal=subtotal, descuento=descuento, total=subtotal - descuento)


# ---- Promociones ----------------------------------------------------------------


def _validar_alcance(alcance: PromocionAlcanceCrear) -> None:
    # El schema (PromocionAlcanceCrear) ya valida esto con @model_validator,
    # pero se revalida acá porque service.py es quien realmente decide las
    # reglas de negocio, no el schema (el schema podría llegar a cambiar
    # sin que nadie note que esta regla dependía de él).
    cantidad = sum(x is not None for x in (alcance.producto_id, alcance.categoria_id, alcance.temporada_id))
    if cantidad != 1:
        raise DomainError("Cada alcance necesita exactamente uno de producto_id, categoria_id o temporada_id")


def crear_promocion(db: Session, datos: PromocionCrear):
    for alcance in datos.alcances:
        _validar_alcance(alcance)
        if alcance.producto_id is not None:
            catalogo_service.obtener_producto(db, alcance.producto_id)  # 404 si no existe

    promocion = Promocion(
        nombre=datos.nombre,
        tipo=datos.tipo,
        valor=datos.valor,
        fecha_inicio=datos.fecha_inicio,
        fecha_fin=datos.fecha_fin,
    )
    promocion.alcances = [
        PromocionAlcance(
            producto_id=alcance.producto_id, categoria_id=alcance.categoria_id, temporada_id=alcance.temporada_id
        )
        for alcance in datos.alcances
    ]
    promocion_repo.crear(db, promocion)  # flush
    db.commit()
    db.refresh(promocion)
    return promocion


def listar_promociones(db: Session, paginacion: ParametrosPaginacion):
    return promocion_repo.listar(db, paginacion)


def obtener_promocion(db: Session, promocion_id: int):
    return promocion_repo.obtener(db, promocion_id)


def actualizar_promocion(db: Session, promocion_id: int, datos: PromocionActualizar):
    promocion = promocion_repo.obtener(db, promocion_id)
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(promocion, campo, valor)
    if promocion.fecha_fin < promocion.fecha_inicio:
        raise DomainError("fecha_fin no puede ser anterior a fecha_inicio")
    db.commit()
    db.refresh(promocion)
    return promocion


def desactivar_promocion(db: Session, promocion_id: int):
    promocion = promocion_repo.obtener(db, promocion_id)
    promocion.activo = False
    db.commit()
    db.refresh(promocion)
    return promocion


# ---- Devoluciones ----------------------------------------------------------------


def registrar_devolucion(db: Session, usuario_id: int, datos: DevolucionCrear) -> Devolucion:
    venta = venta_repo.obtener(db, datos.venta_id)
    detalle_por_id = {linea.id: linea for linea in venta.detalle}

    devolucion = Devolucion(
        codigo=_generar_codigo(db, "DEV", _obtener_devolucion_por_codigo),
        venta_id=venta.id,
        motivo=datos.motivo,
        estado="aprobada",  # esta etapa no tiene un flujo de aprobación aparte
        usuario_id=usuario_id,
    )
    db.add(devolucion)
    db.flush()

    for linea in datos.detalle:
        detalle = detalle_por_id.get(linea.venta_detalle_id)
        if detalle is None:
            raise NoEncontradoError(f"La línea {linea.venta_detalle_id} no pertenece a la venta {venta.id}")

        ya_devuelto = devolucion_repo.cantidad_devuelta(db, linea.venta_detalle_id)
        if ya_devuelto + linea.cantidad > detalle.cantidad:
            raise DomainError(
                f"No se puede devolver más de lo vendido en la línea {linea.venta_detalle_id} "
                f"({ya_devuelto} ya devuelto de {detalle.cantidad})"
            )

        db.add(DevolucionDetalle(devolucion_id=devolucion.id, venta_detalle_id=detalle.id, cantidad=linea.cantidad))

        # La devolución reingresa stock (movimiento tipo 'devolucion'); no
        # reabre la venta ni cambia su estado -- esta etapa no toca pagos.
        inventario_service.registrar_movimiento(
            db,
            variante_id=detalle.variante_id,
            sucursal_id=venta.sucursal_id,
            tipo_movimiento_codigo="devolucion",
            cantidad=linea.cantidad,
            referencia_tipo="devolucion",
            referencia_id=devolucion.id,
            usuario_id=usuario_id,
            commit=False,
        )

    db.commit()
    db.refresh(devolucion)
    return devolucion


def _obtener_devolucion_por_codigo(db: Session, codigo: str) -> Devolucion | None:
    return db.scalar(select(Devolucion).where(Devolucion.codigo == codigo))
