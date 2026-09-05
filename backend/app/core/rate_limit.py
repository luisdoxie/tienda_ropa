"""Limiter compartido de slowapi. Vive acá (no en main.py) para que los
routers puedan importarlo y decorar sus propios endpoints sin depender de
app.main (evita import circular)."""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
