from __future__ import annotations

import datetime as dt
from decimal import Decimal

from sqlalchemy import JSON, Boolean, CheckConstraint, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

# JSON en general (compatible con SQLite, usado en tests); JSONB solo en
# Postgres. Mismo patrón que `probador.models.ActivoProbador.anclajes`.
_TipoJson = JSON().with_variant(JSONB, "postgresql")


class MetodoPago(Base):
    __tablename__ = "metodo_pago"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(25), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(60), nullable=False)
    requiere_pasarela: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    disponible_caja: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    disponible_online: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class EstadoPago(Base):
    __tablename__ = "estado_pago"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(25), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(60), nullable=False)


class Pago(Base):
    __tablename__ = "pago"
    __table_args__ = (CheckConstraint("monto > 0", name="ck_pago_monto"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    venta_id: Mapped[int] = mapped_column(ForeignKey("venta.id"), nullable=False)
    metodo_pago_id: Mapped[int] = mapped_column(ForeignKey("metodo_pago.id"), nullable=False)
    estado_id: Mapped[int] = mapped_column(ForeignKey("estado_pago.id"), nullable=False)
    monto: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    referencia_externa: Mapped[str | None] = mapped_column(String(120))
    fecha: Mapped[dt.datetime] = mapped_column(server_default=func.now())


# Libro de evidencia de cada ida y vuelta con la pasarela: nunca se edita
# ni se borra desde el código (igual que movimiento_inventario). Un
# webhook duplicado agrega una fila más acá, no reemplaza la anterior --
# es justamente lo que permite auditar que llegó dos veces.
class TransaccionPasarela(Base):
    __tablename__ = "transaccion_pasarela"

    id: Mapped[int] = mapped_column(primary_key=True)
    pago_id: Mapped[int] = mapped_column(ForeignKey("pago.id", ondelete="CASCADE"), nullable=False)
    pasarela: Mapped[str] = mapped_column(String(30), nullable=False)
    id_transaccion: Mapped[str | None] = mapped_column(String(120))
    payload_envio: Mapped[dict | None] = mapped_column(_TipoJson)
    payload_respuesta: Mapped[dict | None] = mapped_column(_TipoJson)
    estado: Mapped[str] = mapped_column(String(25), nullable=False)
    creado_en: Mapped[dt.datetime] = mapped_column(server_default=func.now())
