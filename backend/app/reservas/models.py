from __future__ import annotations

import datetime as dt

from sqlalchemy import Boolean, CheckConstraint, Date, ForeignKey, Integer, String, Time, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class EstadoReserva(Base):
    __tablename__ = "estado_reserva"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(25), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(60), nullable=False)
    es_final: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class Reserva(Base):
    __tablename__ = "reserva"
    __table_args__ = (CheckConstraint("hora_visita_hasta > hora_visita_desde", name="ck_reserva_horas"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("cliente.id"), nullable=False)
    sucursal_id: Mapped[int] = mapped_column(ForeignKey("sucursal.id"), nullable=False)
    estado_id: Mapped[int] = mapped_column(ForeignKey("estado_reserva.id"), nullable=False)
    fecha_visita: Mapped[dt.date] = mapped_column(Date, nullable=False)
    hora_visita_desde: Mapped[dt.time] = mapped_column(Time, nullable=False)
    hora_visita_hasta: Mapped[dt.time] = mapped_column(Time, nullable=False)
    fecha_expiracion: Mapped[dt.datetime] = mapped_column(nullable=False)
    observacion: Mapped[str | None] = mapped_column(String(300))
    creado_en: Mapped[dt.datetime] = mapped_column(server_default=func.now())

    detalle: Mapped[list["ReservaDetalle"]] = relationship(
        back_populates="reserva", order_by="ReservaDetalle.id", cascade="all, delete-orphan"
    )
    historial: Mapped[list["ReservaHistorial"]] = relationship(
        back_populates="reserva", order_by="ReservaHistorial.id", cascade="all, delete-orphan"
    )


class ReservaDetalle(Base):
    __tablename__ = "reserva_detalle"
    __table_args__ = (
        CheckConstraint("cantidad > 0", name="ck_reserva_detalle_cantidad"),
        UniqueConstraint("reserva_id", "variante_id", name="uq_reserva_detalle_variante"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    reserva_id: Mapped[int] = mapped_column(ForeignKey("reserva.id", ondelete="CASCADE"), nullable=False)
    variante_id: Mapped[int] = mapped_column(ForeignKey("producto_variante.id"), nullable=False)
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    # NULL = aún no probada. TRUE = el cliente la compra. FALSE = se libera al stock.
    seleccionada: Mapped[bool | None] = mapped_column(Boolean)
    preparada: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    reserva: Mapped[Reserva] = relationship(back_populates="detalle")


class ReservaHistorial(Base):
    __tablename__ = "reserva_historial"

    id: Mapped[int] = mapped_column(primary_key=True)
    reserva_id: Mapped[int] = mapped_column(ForeignKey("reserva.id", ondelete="CASCADE"), nullable=False)
    estado_id: Mapped[int] = mapped_column(ForeignKey("estado_reserva.id"), nullable=False)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"))
    comentario: Mapped[str | None] = mapped_column(String(300))
    creado_en: Mapped[dt.datetime] = mapped_column(server_default=func.now())

    reserva: Mapped[Reserva] = relationship(back_populates="historial")
