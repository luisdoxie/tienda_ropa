from __future__ import annotations

import datetime as dt

from sqlalchemy import Boolean, ForeignKey, SmallInteger, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Categoria(Base):
    __tablename__ = "categoria"

    id: Mapped[int] = mapped_column(primary_key=True)
    categoria_padre_id: Mapped[int | None] = mapped_column(ForeignKey("categoria.id"))
    nombre: Mapped[str] = mapped_column(String(60), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(String(200))
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class Talla(Base):
    __tablename__ = "talla"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    descripcion: Mapped[str | None] = mapped_column(String(40))
    orden: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)


class Color(Base):
    __tablename__ = "color"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    codigo_hex: Mapped[str | None] = mapped_column(String(7))


class Material(Base):
    __tablename__ = "material"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    descripcion: Mapped[str | None] = mapped_column(String(200))


class Temporada(Base):
    __tablename__ = "temporada"
    __table_args__ = (UniqueConstraint("nombre", "anio", name="uq_temporada_nombre_anio"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(60), nullable=False)
    anio: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    fecha_inicio: Mapped[dt.date | None]
    fecha_fin: Mapped[dt.date | None]
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class Coleccion(Base):
    __tablename__ = "coleccion"

    id: Mapped[int] = mapped_column(primary_key=True)
    temporada_id: Mapped[int | None] = mapped_column(ForeignKey("temporada.id"))
    nombre: Mapped[str] = mapped_column(String(80), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(String(300))
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
