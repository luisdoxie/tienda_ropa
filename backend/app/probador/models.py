from __future__ import annotations

import datetime as dt

from sqlalchemy import JSON, CheckConstraint, ForeignKey, Index, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

# JSON en general (compatible con sqlite, usado en tests); JSONB solo en
# Postgres, que es lo que pide el esquema.
_TipoJson = JSON().with_variant(JSONB, "postgresql")


class ActivoProbador(Base):
    __tablename__ = "activo_probador"
    __table_args__ = (
        CheckConstraint("tipo IN ('overlay_2d','flatlay_ia','thumb')", name="ck_activo_probador_tipo"),
        CheckConstraint(
            "estado IN ('pendiente','validado','rechazado')", name="ck_activo_probador_estado"
        ),
        Index(
            "ux_activo_variante_tipo",
            "variante_id",
            "tipo",
            unique=True,
            postgresql_where=text("estado <> 'rechazado'"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    variante_id: Mapped[int] = mapped_column(
        ForeignKey("producto_variante.id", ondelete="CASCADE"), nullable=False
    )
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    # Igual que producto_imagen.url: acá se guarda el public_id de
    # Cloudinary, no la URL completa (ver core/storage.py).
    url: Mapped[str] = mapped_column(Text, nullable=False)
    # Anclajes normalizados 0..1 respecto al tamaño de la imagen:
    # {"hombro_izq": {"x":.., "y":..}, "hombro_der": {...}, "cadera": {...}}
    anclajes: Mapped[dict | None] = mapped_column(_TipoJson)
    ancho_px: Mapped[int | None]
    alto_px: Mapped[int | None]
    estado: Mapped[str] = mapped_column(String(15), nullable=False, default="pendiente")
    creado_por: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"))
    creado_en: Mapped[dt.datetime] = mapped_column(server_default=func.now())


class ProbadorGeneracion(Base):
    """Caché del modo generativo: evita pagar dos veces la misma
    combinación foto+prenda. La foto original del cliente NUNCA se
    guarda acá ni en ningún otro lado — solo su hash y, si la
    generación tuvo éxito, la URL del resultado en Cloudinary."""

    __tablename__ = "probador_generacion"
    __table_args__ = (
        CheckConstraint(
            "estado IN ('en_proceso','completado','fallido')", name="ck_probador_generacion_estado"
        ),
        Index("ix_generacion_cache", "hash_foto", "variante_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int | None] = mapped_column(ForeignKey("cliente.id"))
    variante_id: Mapped[int] = mapped_column(ForeignKey("producto_variante.id"), nullable=False)
    hash_foto: Mapped[str] = mapped_column(String(64), nullable=False)
    url_resultado: Mapped[str | None] = mapped_column(Text)
    proveedor: Mapped[str | None] = mapped_column(String(30))
    estado: Mapped[str] = mapped_column(String(15), nullable=False, default="en_proceso")
    mensaje_error: Mapped[str | None] = mapped_column(String(300))
    creado_en: Mapped[dt.datetime] = mapped_column(server_default=func.now())


class SesionProbador(Base):
    """Un registro por cada vez que un cliente usa el probador (espejo o
    generativo). Es la métrica de uso y, más adelante, el alimento del
    recomendador (paquete `inteligencia`)."""

    __tablename__ = "sesion_probador"
    __table_args__ = (CheckConstraint("modo IN ('espejo','generativo')", name="ck_sesion_probador_modo"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int | None] = mapped_column(ForeignKey("cliente.id"))
    variante_id: Mapped[int] = mapped_column(ForeignKey("producto_variante.id"), nullable=False)
    modo: Mapped[str] = mapped_column(String(15), nullable=False)
    duracion_seg: Mapped[int | None]
    creado_en: Mapped[dt.datetime] = mapped_column(server_default=func.now())
