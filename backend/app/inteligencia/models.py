from __future__ import annotations

import datetime as dt

from sqlalchemy import JSON, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

# JSON en general (compatible con sqlite, usado en tests); JSONB solo en
# Postgres, que es lo que pide el esquema (ver probador/models.py, mismo
# patrón).
_TipoJson = JSON().with_variant(JSONB, "postgresql")


class ConsultaVoz(Base):
    """Log de cada búsqueda por voz (P6.1): qué se transcribió, qué filtros
    se aplicaron (los haya resuelto Groq o el fallback de texto plano) y
    cuántos resultados dio. `cliente_id` es nullable a propósito: la
    búsqueda por voz admite uso anónimo, igual que /catalogo/buscar."""

    __tablename__ = "consulta_voz"

    id: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int | None] = mapped_column(ForeignKey("cliente.id"))
    texto_transcrito: Mapped[str] = mapped_column(Text, nullable=False)
    filtros_json: Mapped[dict | None] = mapped_column(_TipoJson)
    cantidad_resultados: Mapped[int | None]
    creado_en: Mapped[dt.datetime] = mapped_column(server_default=func.now())
