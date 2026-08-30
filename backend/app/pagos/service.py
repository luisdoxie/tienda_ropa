"""Pagos: iniciar_pago_pasarela()/pagar_en_caja() crean el `pago`;
procesar_webhook() es quien lo resuelve (aprobado/rechazado) y, recién en
ese momento, dispara ventas.service.confirmar_venta()/anular_venta() --
"solo cuando el pago pasa a aprobado se confirma la venta y se descuenta
el stock" (P5.2).

Idempotencia del webhook: cada llamada agrega su propia fila de evidencia
a `transaccion_pasarela` (eso nunca se salta, es la auditoría), pero el
efecto de negocio (confirmar/anular la venta) solo se dispara la PRIMERA
vez que un pago sale de 'iniciado'. Un webhook repetido (red flaky, la
pasarela reintentando) encuentra el pago ya resuelto y no vuelve a tocar
la venta ni el stock -- ver `_ya_resuelto` y el test/"Revisar" de curl
duplicado.
"""

from __future__ import annotations

import json
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictoError, DomainError, NoEncontradoError, PermisoDenegadoError
from app.organizacion import service as organizacion_service
from app.pagos.models import Pago, TransaccionPasarela
from app.pagos.pasarela import obtener_pasarela
from app.pagos.repository import EstadoPagoRepository, MetodoPagoRepository, PagoRepository, TransaccionPasarelaRepository
from app.pagos.schemas import PagoCajaRequest, PagoIniciarRequest
from app.ventas import service as ventas_service

metodo_repo = MetodoPagoRepository()
estado_repo = EstadoPagoRepository()
pago_repo = PagoRepository()
transaccion_repo = TransaccionPasarelaRepository()


def iniciar_pago_pasarela(db: Session, usuario_id: int, datos: PagoIniciarRequest) -> tuple[Pago, str]:
    venta = ventas_service.obtener_comprobante(db, datos.venta_id, usuario_id)  # valida dueño o staff

    metodo = metodo_repo.obtener_por_codigo(db, datos.metodo_pago)
    if not metodo.requiere_pasarela:
        raise DomainError(f"'{metodo.codigo}' no es un método por pasarela, usá /pagos/caja")

    estado_iniciado = estado_repo.obtener_por_codigo(db, "iniciado")
    pago = Pago(venta_id=venta.id, metodo_pago_id=metodo.id, estado_id=estado_iniciado.id, monto=venta.total)
    pago_repo.crear(db, pago)  # flush: pago.id ya disponible

    pasarela = obtener_pasarela(metodo.codigo)
    try:
        resultado = pasarela.iniciar_pago(monto=venta.total, referencia=venta.codigo)
    except RuntimeError as exc:
        # No deja el pago en 'iniciado' colgado si la pasarela real (p.
        # ej. PayPal) no respondió: no tiene una transacción real detrás.
        db.rollback()
        raise DomainError(str(exc)) from exc
    pago.referencia_externa = resultado.id_transaccion

    payload_envio = {"monto": str(venta.total), "referencia": venta.codigo}
    payload_respuesta = {"id_transaccion": resultado.id_transaccion, "url_redireccion": resultado.url_redireccion}
    transaccion_repo.crear(
        db,
        TransaccionPasarela(
            pago_id=pago.id,
            pasarela=metodo.codigo,
            id_transaccion=resultado.id_transaccion,
            payload_envio=payload_envio,
            payload_respuesta=payload_respuesta,
            estado="iniciado",
        ),
    )

    db.commit()
    db.refresh(pago)
    return pago, resultado.url_redireccion


def pagar_en_caja(db: Session, usuario_id: int, datos: PagoCajaRequest) -> tuple[Pago, Decimal | None]:
    empleado = organizacion_service.obtener_empleado_por_usuario(db, usuario_id)
    if empleado is None:
        raise PermisoDenegadoError("Este usuario no es un empleado, no puede cobrar en caja")

    venta = ventas_service.obtener_venta(db, datos.venta_id)
    metodo = metodo_repo.obtener_por_codigo(db, datos.metodo_pago)
    if not metodo.disponible_caja:
        raise DomainError(f"'{metodo.codigo}' no está disponible en caja")

    cambio: Decimal | None = None
    if metodo.codigo == "efectivo":
        if datos.monto_recibido is None:
            raise DomainError("El pago en efectivo necesita monto_recibido")
        if datos.monto_recibido < venta.total:
            raise DomainError(f"El monto recibido ({datos.monto_recibido}) no cubre el total ({venta.total})")
        cambio = datos.monto_recibido - venta.total

    estado_aprobado = estado_repo.obtener_por_codigo(db, "aprobado")
    pago = Pago(venta_id=venta.id, metodo_pago_id=metodo.id, estado_id=estado_aprobado.id, monto=venta.total)
    pago_repo.crear(db, pago)  # flush

    # El pago en caja se aprueba en el momento: no hay pasarela ni
    # webhook, así que acá mismo se dispara la confirmación de la venta.
    ventas_service.confirmar_venta(db, venta.id, usuario_id=usuario_id, commit=False)

    db.commit()
    db.refresh(pago)
    return pago, cambio


def _ya_resuelto(codigo_estado: str) -> bool:
    return codigo_estado != "iniciado"


def _resolver_pago(
    db: Session,
    pago: Pago,
    *,
    pasarela_codigo: str,
    id_transaccion: str | None,
    estado_resultado: str,
    payload_respuesta: dict,
    commit: bool,
) -> Pago:
    """Registra la evidencia y, si el pago todavía estaba 'iniciado',
    aplica el resultado (aprobado/rechazado) UNA sola vez. La usan tanto
    el webhook como el polling activo de obtener_estado_pago(): es el
    único lugar que decide si un resultado ya se aplicó o no (ahí vive la
    idempotencia)."""
    estado_actual = estado_repo.obtener(db, pago.estado_id)

    transaccion_repo.crear(
        db,
        TransaccionPasarela(
            pago_id=pago.id,
            pasarela=pasarela_codigo,
            id_transaccion=id_transaccion,
            payload_envio=None,
            payload_respuesta=payload_respuesta,
            estado=estado_resultado,
        ),
    )

    if _ya_resuelto(estado_actual.codigo):
        # Idempotencia: este pago ya salió de 'iniciado' antes. No se
        # vuelve a confirmar/anular la venta ni a tocar el stock.
        if commit:
            db.commit()
            db.refresh(pago)
        else:
            db.flush()
        return pago

    if estado_resultado in ("aprobado", "rechazado"):
        estado_nuevo = estado_repo.obtener_por_codigo(db, estado_resultado)
        pago.estado_id = estado_nuevo.id
        if estado_resultado == "aprobado":
            ventas_service.confirmar_venta(db, pago.venta_id, commit=False)
        else:
            ventas_service.anular_venta(db, pago.venta_id, commit=False)
    # 'iniciado' repetido (sin novedad real): no cambia nada más.

    if commit:
        db.commit()
        db.refresh(pago)
    else:
        db.flush()
    return pago


def procesar_webhook(db: Session, pasarela_codigo: str, payload_crudo: bytes, firma: str | None) -> Pago:
    # `pasarela_codigo` viene de la URL (path param), sin validar contra
    # la base -- a diferencia de iniciar_pago_pasarela, que ya lo saca de
    # un metodo_pago existente. Acá si no es una pasarela real, es un 404,
    # no un error 500.
    try:
        pasarela = obtener_pasarela(pasarela_codigo)
    except ValueError as exc:
        raise NoEncontradoError(f"No existe la pasarela '{pasarela_codigo}'") from exc

    if not pasarela.verificar_firma(payload_crudo, firma):
        raise PermisoDenegadoError("Firma de webhook inválida")

    try:
        payload = json.loads(payload_crudo)
    except json.JSONDecodeError as exc:
        raise DomainError("El body del webhook no es JSON válido") from exc

    resultado = pasarela.interpretar_webhook(payload)

    transaccion_original = transaccion_repo.obtener_por_id_transaccion(db, pasarela_codigo, resultado.id_transaccion)
    if transaccion_original is None:
        raise NoEncontradoError(f"No hay ningún pago iniciado con id_transaccion '{resultado.id_transaccion}'")

    pago = pago_repo.obtener(db, transaccion_original.pago_id)
    return _resolver_pago(
        db,
        pago,
        pasarela_codigo=pasarela_codigo,
        id_transaccion=resultado.id_transaccion,
        estado_resultado=resultado.estado,
        payload_respuesta=payload,
        commit=True,
    )


def obtener_estado_pago(db: Session, usuario_id: int, pago_id: int) -> Pago:
    pago = pago_repo.obtener(db, pago_id)
    ventas_service.obtener_comprobante(db, pago.venta_id, usuario_id)  # valida dueño o staff, 404 si no existe

    estado_actual = estado_repo.obtener(db, pago.estado_id)
    if estado_actual.codigo != "iniciado":
        return pago

    # Todavía no llegó (o nunca llegó) el webhook: pregunta activamente a
    # la pasarela, por si acá se enteran antes que por webhook.
    primera = db.scalar(
        select(TransaccionPasarela)
        .where(TransaccionPasarela.pago_id == pago.id)
        .order_by(TransaccionPasarela.creado_en.asc())
        .limit(1)
    )
    if primera is None or primera.id_transaccion is None:
        return pago

    pasarela = obtener_pasarela(primera.pasarela)
    try:
        estado_pasarela = pasarela.consultar_estado(primera.id_transaccion)
    except RuntimeError:
        # Best-effort: si la pasarela real no responde ahora, se devuelve
        # el último estado guardado en vez de romper el polling del cliente.
        return pago
    if estado_pasarela == "iniciado":
        return pago  # sin novedad

    return _resolver_pago(
        db,
        pago,
        pasarela_codigo=primera.pasarela,
        id_transaccion=primera.id_transaccion,
        estado_resultado=estado_pasarela,
        payload_respuesta={"origen": "consultar_estado", "estado": estado_pasarela},
        commit=True,
    )


def anular_pago(db: Session, pago_id: int) -> Pago:
    """El permiso ('pagos.gestionar') ya lo gatea el router, como el
    resto de las acciones de staff en este proyecto -- acá no se
    revalida."""
    pago = pago_repo.obtener(db, pago_id)
    estado_actual = estado_repo.obtener(db, pago.estado_id)
    if estado_actual.codigo != "aprobado":
        raise ConflictoError(f"Solo se puede anular un pago 'aprobado' (está '{estado_actual.codigo}')")

    estado_reembolsado = estado_repo.obtener_por_codigo(db, "reembolsado")
    pago.estado_id = estado_reembolsado.id

    ventas_service.anular_venta(db, pago.venta_id, commit=False)

    db.commit()
    db.refresh(pago)
    return pago
