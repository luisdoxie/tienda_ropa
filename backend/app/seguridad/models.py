from __future__ import annotations

import datetime as dt

from sqlalchemy import Boolean, CheckConstraint, Column, ForeignKey, String, Table, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

rol_permiso = Table(
    "rol_permiso",
    Base.metadata,
    Column("rol_id", ForeignKey("rol.id", ondelete="CASCADE"), primary_key=True),
    Column("permiso_id", ForeignKey("permiso.id", ondelete="CASCADE"), primary_key=True),
)

usuario_rol = Table(
    "usuario_rol",
    Base.metadata,
    Column("usuario_id", ForeignKey("usuario.id", ondelete="CASCADE"), primary_key=True),
    Column("rol_id", ForeignKey("rol.id"), primary_key=True),
)


class Rol(Base):
    __tablename__ = "rol"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    descripcion: Mapped[str | None] = mapped_column(String(200))
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    permisos: Mapped[list["Permiso"]] = relationship(secondary=rol_permiso, back_populates="roles")


class Permiso(Base):
    __tablename__ = "permiso"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    modulo: Mapped[str] = mapped_column(String(40), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(String(200))

    roles: Mapped[list[Rol]] = relationship(secondary=rol_permiso, back_populates="permisos")


class Usuario(Base):
    __tablename__ = "usuario"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(60), nullable=False)
    apellido: Mapped[str] = mapped_column(String(60), nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    telefono: Mapped[str | None] = mapped_column(String(20))
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    ultimo_acceso: Mapped[dt.datetime | None]
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    creado_en: Mapped[dt.datetime] = mapped_column(server_default=func.now())
    actualizado_en: Mapped[dt.datetime | None]

    roles: Mapped[list[Rol]] = relationship(secondary=usuario_rol)
    cliente: Mapped["Cliente | None"] = relationship(back_populates="usuario", uselist=False)


class Cliente(Base):
    __tablename__ = "cliente"
    __table_args__ = (
        CheckConstraint("estatura_cm BETWEEN 100 AND 250", name="ck_cliente_estatura"),
        CheckConstraint(
            "preferencia_ajuste IN ('ajustado','regular','holgado')",
            name="ck_cliente_preferencia_ajuste",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"), unique=True, nullable=False)
    ci_nit: Mapped[str | None] = mapped_column(String(20))
    razon_social: Mapped[str | None] = mapped_column(String(120))
    fecha_nacimiento: Mapped[dt.date | None]
    estatura_cm: Mapped[int | None]
    preferencia_ajuste: Mapped[str | None] = mapped_column(String(15))
    acepta_datos_foto: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    creado_en: Mapped[dt.datetime] = mapped_column(server_default=func.now())

    usuario: Mapped[Usuario] = relationship(back_populates="cliente")
