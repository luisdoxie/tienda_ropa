"""Interfaz de las pasarelas de pago. Todo lo que sabe hablar con un
proveedor externo de pagos vive detrás de `PasarelaBase`. El resto del
paquete (`service.py`) solo conoce esta interfaz, nunca a la pasarela
concreta -- agregar una pasarela nueva es escribir una clase acá, no
tocar el flujo de pago/webhook/confirmación de la venta.

LibelulaGateway y PayPalGateway son SIMULADORES de sandbox: este proyecto
no tiene credenciales reales de Libélula ni de PayPal configuradas (ver
docs/plan_desarrollo_fashionstore.md, que las deja como paso manual
pendiente), así que ninguna de las dos llama a un servidor externo de
verdad. Lo que sí implementan de punta a punta, igual que una integración
real, es la forma del contrato: iniciar_pago() arma una referencia de
transacción y una URL de retorno, y verificar_firma()/interpretar_webhook()
validan y leen un webhook con la misma disciplina (HMAC sobre el body
crudo) que exigiría una pasarela real. Cuando haya credenciales reales,
el reemplazo es SOLO el cuerpo de estos dos métodos por llamadas HTTP a
la API real -- la interfaz y el resto del sistema no cambian.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal

from app.core.config import get_settings


@dataclass(frozen=True)
class ResultadoIniciar:
    id_transaccion: str
    url_redireccion: str


@dataclass(frozen=True)
class ResultadoWebhook:
    id_transaccion: str
    estado: str  # código de estado_pago: 'aprobado' o 'rechazado'


class PasarelaBase(ABC):
    nombre: str

    @abstractmethod
    def iniciar_pago(self, *, monto: Decimal, referencia: str) -> ResultadoIniciar:
        """Arranca el pago del lado de la pasarela y devuelve el id de
        transacción y la URL a la que hay que redirigir al cliente."""
        raise NotImplementedError

    @abstractmethod
    def consultar_estado(self, id_transaccion: str) -> str:
        """Le pregunta a la pasarela el estado actual de una transacción
        (para el polling de GET /pagos/{id}/estado cuando todavía no llegó
        el webhook). Devuelve un código de estado_pago."""
        raise NotImplementedError

    @abstractmethod
    def verificar_firma(self, payload_crudo: bytes, firma: str | None) -> bool:
        """Valida que el webhook realmente venga de la pasarela antes de
        confiar en su contenido."""
        raise NotImplementedError

    @abstractmethod
    def interpretar_webhook(self, payload: dict) -> ResultadoWebhook:
        """Ya verificada la firma, extrae el id de transacción y el
        estado resultante del payload (cada pasarela lo estructura
        distinto)."""
        raise NotImplementedError


def _firmar(secreto: str, payload_crudo: bytes) -> str:
    return hmac.new(secreto.encode("utf-8"), payload_crudo, hashlib.sha256).hexdigest()


class LibelulaGateway(PasarelaBase):
    nombre = "libelula"

    def __init__(self) -> None:
        self._secreto = get_settings().libelula_webhook_secret

    def iniciar_pago(self, *, monto: Decimal, referencia: str) -> ResultadoIniciar:
        id_transaccion = f"LIB-{secrets.token_hex(8).upper()}"
        return ResultadoIniciar(
            id_transaccion=id_transaccion,
            url_redireccion=f"https://sandbox.libelula.bo/checkout/{id_transaccion}",
        )

    def consultar_estado(self, id_transaccion: str) -> str:
        # Sandbox sin servidor real detrás: sin webhook no hay forma de
        # saber que cambió, así que "sigue iniciado" es la respuesta
        # honesta (no inventa una aprobación que nunca llegó).
        return "iniciado"

    def verificar_firma(self, payload_crudo: bytes, firma: str | None) -> bool:
        if not firma:
            return False
        return hmac.compare_digest(_firmar(self._secreto, payload_crudo), firma)

    def interpretar_webhook(self, payload: dict) -> ResultadoWebhook:
        return ResultadoWebhook(id_transaccion=payload["id_transaccion"], estado=payload["estado"])


class PayPalGateway(PasarelaBase):
    nombre = "paypal"

    def __init__(self) -> None:
        self._secreto = get_settings().paypal_webhook_secret

    def iniciar_pago(self, *, monto: Decimal, referencia: str) -> ResultadoIniciar:
        id_transaccion = f"PP-{secrets.token_hex(8).upper()}"
        return ResultadoIniciar(
            id_transaccion=id_transaccion,
            url_redireccion=f"https://sandbox.paypal.com/checkoutnow?token={id_transaccion}",
        )

    def consultar_estado(self, id_transaccion: str) -> str:
        return "iniciado"

    def verificar_firma(self, payload_crudo: bytes, firma: str | None) -> bool:
        if not firma:
            return False
        return hmac.compare_digest(_firmar(self._secreto, payload_crudo), firma)

    def interpretar_webhook(self, payload: dict) -> ResultadoWebhook:
        return ResultadoWebhook(id_transaccion=payload["id_transaccion"], estado=payload["estado"])


_PASARELAS: dict[str, type[PasarelaBase]] = {
    "libelula": LibelulaGateway,
    "paypal": PayPalGateway,
}


def obtener_pasarela(codigo: str) -> PasarelaBase:
    clase = _PASARELAS.get(codigo)
    if clase is None:
        raise ValueError(f"No hay pasarela registrada para '{codigo}'")
    return clase()
