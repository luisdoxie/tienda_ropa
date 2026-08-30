from __future__ import annotations

import datetime as dt
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Numeric, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ZonaEnvio(Base):
    __tablename__ = "zona_envio"
    __table_args__ = (CheckConstraint("tarifa_base >= 0", name="ck_zona_envio_tarifa_base"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    ciudad_id: Mapped[int] = mapped_column(ForeignKey("ciudad.id"), nullable=False)
    nombre: Mapped[str] = mapped_column(String(60), nullable=False)
    anillo_desde: Mapped[int | None] = mapped_column(SmallInteger)
    anillo_hasta: Mapped[int | None] = mapped_column(SmallInteger)
    tarifa_base: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class ReglaTarifaEnvio(Base):
    __tablename__ = "regla_tarifa_envio"

    id: Mapped[int] = mapped_column(primary_key=True)
    zona_envio_id: Mapped[int] = mapped_column(ForeignKey("zona_envio.id", ondelete="CASCADE"), nullable=False)
    peso_desde_kg: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False, default=0)
    peso_hasta_kg: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    recargo: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)


class DireccionCliente(Base):
    __tablename__ = "direccion_cliente"

    id: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("cliente.id", ondelete="CASCADE"), nullable=False)
    zona_envio_id: Mapped[int | None] = mapped_column(ForeignKey("zona_envio.id"))
    alias: Mapped[str | None] = mapped_column(String(40))
    direccion: Mapped[str] = mapped_column(String(200), nullable=False)
    referencia: Mapped[str | None] = mapped_column(String(200))
    latitud: Mapped[Decimal | None] = mapped_column(Numeric(10, 7))
    longitud: Mapped[Decimal | None] = mapped_column(Numeric(10, 7))
    es_principal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class Envio(Base):
    __tablename__ = "envio"
    __table_args__ = (
        CheckConstraint(
            "estado IN ('programado','en_ruta','entregado','fallido')", name="ck_envio_estado"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    venta_id: Mapped[int] = mapped_column(ForeignKey("venta.id"), unique=True, nullable=False)
    direccion_id: Mapped[int] = mapped_column(ForeignKey("direccion_cliente.id"), nullable=False)
    zona_envio_id: Mapped[int] = mapped_column(ForeignKey("zona_envio.id"), nullable=False)
    costo: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    peso_kg: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="programado")
    fecha_programada: Mapped[dt.datetime | None]
    fecha_entrega: Mapped[dt.datetime | None]
    repartidor: Mapped[str | None] = mapped_column(String(80))
