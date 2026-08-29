from __future__ import annotations

import datetime as dt

from sqlalchemy import Boolean, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Notificacion(Base):
    __tablename__ = "notificacion"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"), nullable=False)
    titulo: Mapped[str] = mapped_column(String(120), nullable=False)
    mensaje: Mapped[str | None] = mapped_column(String(400))
    tipo: Mapped[str | None] = mapped_column(String(30))
    referencia_id: Mapped[int | None]
    leida: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    creado_en: Mapped[dt.datetime] = mapped_column(server_default=func.now())
