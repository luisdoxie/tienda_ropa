"""Entregas: zona_envio/regla_tarifa_envio son el tarifario (kilometraje por
anillo + recargo por peso), direccion_cliente es la libreta de direcciones
del cliente, y envio es el seguimiento logístico de una venta ya creada.

cotizar_envio() es un cálculo puro (no persiste nada, no toca la base más
que para leer zona/reglas): existe para que el checkout muestre el costo de
envío ANTES de crear la venta. Ese mismo costo es el que el cliente manda en
`VentaDigitalCrear.costo_envio` (ver app/ventas/schemas.py) al confirmar la
compra -- por eso crear_envio() no vuelve a calcular un costo, usa
`venta.costo_envio` tal cual quedó grabado en la venta.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import ConflictoError, DomainError, NoEncontradoError
from app.entregas.models import DireccionCliente, Envio, ZonaEnvio
from app.entregas.repository import DireccionClienteRepository, EnvioRepository, ZonaEnvioRepository
from app.entregas.schemas import (
    CotizarEnvioRequest,
    CotizarEnvioRespuesta,
    DireccionClienteActualizar,
    DireccionClienteCrear,
    EnvioCrear,
    EnvioEstadoActualizar,
)
from app.seguridad import service as seguridad_service
from app.ventas import service as ventas_service

zona_repo = ZonaEnvioRepository()
direccion_repo = DireccionClienteRepository()
envio_repo = EnvioRepository()

# programado -> en_ruta -> entregado | fallido. 'entregado' y 'fallido' son
# terminales: un envío que ya llegó (o falló) no vuelve a moverse de ahí.
_TRANSICIONES: dict[str, set[str]] = {
    "programado": {"en_ruta", "fallido"},
    "en_ruta": {"entregado", "fallido"},
    "entregado": set(),
    "fallido": set(),
}


def _peso_pedido(cantidad_prendas: int) -> Decimal:
    return get_settings().peso_promedio_prenda_kg * cantidad_prendas


def _calcular_costo(db: Session, zona: ZonaEnvio, peso_kg: Decimal) -> tuple[Decimal, Decimal]:
    """(recargo_por_peso, costo_total). El recargo es el de la regla de la
    zona cuyo rango [peso_desde_kg, peso_hasta_kg] contiene el peso del
    pedido; sin regla que lo cubra, no hay recargo por peso."""
    recargo = Decimal("0")
    for regla in zona_repo.listar_reglas(db, zona.id):
        if peso_kg >= regla.peso_desde_kg and (regla.peso_hasta_kg is None or peso_kg <= regla.peso_hasta_kg):
            recargo = regla.recargo
            break
    return recargo, zona.tarifa_base + recargo


def _direccion_con_zona(db: Session, direccion_id: int) -> tuple[DireccionCliente, ZonaEnvio]:
    direccion = direccion_repo.obtener(db, direccion_id)
    if direccion.zona_envio_id is None:
        raise DomainError("Esta dirección no tiene una zona de envío asignada")
    zona = zona_repo.obtener(db, direccion.zona_envio_id)
    return direccion, zona


def cotizar_envio(db: Session, datos: CotizarEnvioRequest) -> CotizarEnvioRespuesta:
    _direccion, zona = _direccion_con_zona(db, datos.direccion_id)
    peso = _peso_pedido(datos.cantidad_prendas)
    recargo, costo = _calcular_costo(db, zona, peso)
    return CotizarEnvioRespuesta(
        zona_envio_id=zona.id,
        zona_nombre=zona.nombre,
        peso_kg=peso,
        tarifa_base=zona.tarifa_base,
        recargo_peso=recargo,
        costo=costo,
    )


# ---- Direcciones de cliente (recurso propio del cliente logueado) -------------


def listar_mis_direcciones(db: Session, usuario_id: int) -> list[DireccionCliente]:
    cliente = seguridad_service.obtener_perfil_cliente(db, usuario_id)
    return direccion_repo.listar_por_cliente(db, cliente.id)


def crear_mi_direccion(db: Session, usuario_id: int, datos: DireccionClienteCrear) -> DireccionCliente:
    cliente = seguridad_service.obtener_perfil_cliente(db, usuario_id)
    if datos.zona_envio_id is not None:
        zona_repo.obtener(db, datos.zona_envio_id)  # 404 si no existe o está inactiva
    return direccion_repo.crear(db, cliente.id, datos)


def _validar_acceso_direccion(db: Session, direccion: DireccionCliente, usuario_id: int) -> None:
    cliente = seguridad_service.obtener_perfil_cliente(db, usuario_id)
    if cliente is None or direccion.cliente_id != cliente.id:
        # 404, no 403: no confirma a otro cliente que el id existe.
        raise NoEncontradoError("Dirección no encontrada")


def actualizar_mi_direccion(
    db: Session, usuario_id: int, direccion_id: int, datos: DireccionClienteActualizar
) -> DireccionCliente:
    direccion = direccion_repo.obtener(db, direccion_id)
    _validar_acceso_direccion(db, direccion, usuario_id)
    if datos.zona_envio_id is not None:
        zona_repo.obtener(db, datos.zona_envio_id)
    return direccion_repo.actualizar(db, direccion_id, datos)


def desactivar_mi_direccion(db: Session, usuario_id: int, direccion_id: int) -> DireccionCliente:
    direccion = direccion_repo.obtener(db, direccion_id)
    _validar_acceso_direccion(db, direccion, usuario_id)
    return direccion_repo.desactivar(db, direccion_id)


# ---- Envíos -------------------------------------------------------------------


def crear_envio(db: Session, usuario_id: int, datos: EnvioCrear) -> Envio:
    venta = ventas_service.obtener_comprobante(db, datos.venta_id, usuario_id)  # valida dueño o staff
    if envio_repo.obtener_por_venta(db, venta.id) is not None:
        raise ConflictoError("Esta venta ya tiene un envío registrado")

    direccion, zona = _direccion_con_zona(db, datos.direccion_id)
    if venta.cliente_id is None or direccion.cliente_id != venta.cliente_id:
        raise DomainError("La dirección no pertenece al cliente de esta venta")

    cantidad_prendas = sum(linea.cantidad for linea in venta.detalle)
    envio = Envio(
        venta_id=venta.id,
        direccion_id=direccion.id,
        zona_envio_id=zona.id,
        # El costo ya quedó fijado en la venta (lo que devolvió /cotizar en
        # el checkout, ver docstring del módulo): acá no se recalcula.
        costo=venta.costo_envio,
        peso_kg=_peso_pedido(cantidad_prendas),
        estado="programado",
    )
    return envio_repo.crear(db, envio)


def actualizar_estado_envio(db: Session, envio_id: int, datos: EnvioEstadoActualizar) -> Envio:
    envio = envio_repo.obtener(db, envio_id)
    permitidos = _TRANSICIONES.get(envio.estado, set())
    if datos.estado not in permitidos:
        raise ConflictoError(f"No se puede pasar de '{envio.estado}' a '{datos.estado}'")

    envio.estado = datos.estado
    if datos.repartidor is not None:
        envio.repartidor = datos.repartidor
    if datos.estado == "en_ruta" and envio.fecha_programada is None:
        envio.fecha_programada = dt.datetime.now(dt.timezone.utc)
    elif datos.estado == "entregado":
        envio.fecha_entrega = dt.datetime.now(dt.timezone.utc)

    db.commit()
    db.refresh(envio)
    return envio
