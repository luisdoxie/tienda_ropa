"""Limiter compartido de slowapi. Vive acá (no en main.py) para que los
routers puedan importarlo y decorar sus propios endpoints sin depender de
app.main (evita import circular)."""

from fastapi import Request
from slowapi import Limiter

from app.core.config import get_settings


def _direccion_cliente(request: Request) -> str:
    """En producción (Railway) la app corre detrás de un proxy: sin esto,
    request.client.host es la IP del proxy, no la del cliente real, y todos
    los clientes comparten el mismo balde de rate limit. `X-Forwarded-For`
    trae la IP real como primer valor -- pero solo se confía en ese header
    fuera de 'local', donde no hay proxy y cualquiera podría falsificarlo
    para evadir el límite (B-9 de la auditoría)."""
    if get_settings().environment != "local":
        adelantada = request.headers.get("x-forwarded-for")
        if adelantada:
            return adelantada.split(",")[0].strip()
    if not request.client or not request.client.host:
        return "127.0.0.1"
    return request.client.host


limiter = Limiter(key_func=_direccion_cliente)
