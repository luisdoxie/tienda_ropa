from __future__ import annotations

import datetime as dt
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Numeric,
    SmallInteger,
    String,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Ciudad(Base):
    __tablename__ = "ciudad"
    __table_args__ = (UniqueConstraint("nombre", "departamento", name="uq_ciudad_nombre_departamento"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(60), nullable=False)
    departamento: Mapped[str | None] = mapped_column(String(60))
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class Sucursal(Base):
    __tablename__ = "sucursal"

    id: Mapped[int] = mapped_column(primary_key=True)
    ciudad_id: Mapped[int] = mapped_column(ForeignKey("ciudad.id"), nullable=False)
    codigo: Mapped[str] = mapped_column(String(15), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(80), nullable=False)
    direccion: Mapped[str] = mapped_column(String(200), nullable=False)
    telefono: Mapped[str | None] = mapped_column(String(20))
    latitud: Mapped[Decimal | None] = mapped_column(Numeric(10, 7))
    longitud: Mapped[Decimal | None] = mapped_column(Numeric(10, 7))
    es_deposito: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    creado_en: Mapped[dt.datetime] = mapped_column(server_default=func.now())


class HorarioSucursal(Base):
    __tablename__ = "horario_sucursal"
    __table_args__ = (
        CheckConstraint("dia_semana BETWEEN 1 AND 7", name="ck_horario_dia_semana"),
        CheckConstraint("hora_cierre > hora_apertura", name="ck_horario_cierre_despues_apertura"),
        UniqueConstraint("sucursal_id", "dia_semana", name="uq_horario_sucursal_dia"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    sucursal_id: Mapped[int] = mapped_column(ForeignKey("sucursal.id", ondelete="CASCADE"), nullable=False)
    dia_semana: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    hora_apertura: Mapped[dt.time] = mapped_column(Time, nullable=False)
    hora_cierre: Mapped[dt.time] = mapped_column(Time, nullable=False)


class Empleado(Base):
    __tablename__ = "empleado"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"), unique=True, nullable=False)
    sucursal_id: Mapped[int | None] = mapped_column(ForeignKey("sucursal.id"))
    ci: Mapped[str | None] = mapped_column(String(20))
    cargo: Mapped[str | None] = mapped_column(String(60))
    fecha_ingreso: Mapped[dt.date | None]
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
