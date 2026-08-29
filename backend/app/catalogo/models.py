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
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

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


class Producto(Base):
    __tablename__ = "producto"
    __table_args__ = (
        CheckConstraint("genero IN ('hombre','mujer','unisex','nino')", name="ck_producto_genero"),
        CheckConstraint("precio_base >= 0", name="ck_producto_precio_base"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text)
    categoria_id: Mapped[int] = mapped_column(ForeignKey("categoria.id"), nullable=False)
    material_id: Mapped[int | None] = mapped_column(ForeignKey("material.id"))
    temporada_id: Mapped[int | None] = mapped_column(ForeignKey("temporada.id"))
    coleccion_id: Mapped[int | None] = mapped_column(ForeignKey("coleccion.id"))
    genero: Mapped[str] = mapped_column(String(15), nullable=False, default="unisex")
    precio_base: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    # Marca si la categoría admite probador virtual (torso superior).
    admite_probador: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    creado_en: Mapped[dt.datetime] = mapped_column(server_default=func.now())
    creado_por: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"))


# La variante es la unidad real de negocio: el stock, el precio final, la
# reserva y la venta cuelgan de acá, nunca del producto.
class ProductoVariante(Base):
    __tablename__ = "producto_variante"
    __table_args__ = (
        CheckConstraint("precio IS NULL OR precio >= 0", name="ck_variante_precio"),
        UniqueConstraint("producto_id", "talla_id", "color_id", name="uq_variante_producto_talla_color"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    producto_id: Mapped[int] = mapped_column(ForeignKey("producto.id", ondelete="CASCADE"), nullable=False)
    talla_id: Mapped[int] = mapped_column(ForeignKey("talla.id"), nullable=False)
    color_id: Mapped[int] = mapped_column(ForeignKey("color.id"), nullable=False)
    sku: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    codigo_barras: Mapped[str | None] = mapped_column(String(40), unique=True)
    precio: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    producto: Mapped[Producto] = relationship()


class ProductoImagen(Base):
    __tablename__ = "producto_imagen"

    id: Mapped[int] = mapped_column(primary_key=True)
    producto_id: Mapped[int] = mapped_column(ForeignKey("producto.id", ondelete="CASCADE"), nullable=False)
    color_id: Mapped[int | None] = mapped_column(ForeignKey("color.id"))
    url: Mapped[str] = mapped_column(Text, nullable=False)
    orden: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    es_principal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


# Rangos corporales por talla. Base de la recomendación de talla (CU-52).
class TablaMedida(Base):
    __tablename__ = "tabla_medida"
    __table_args__ = (
        CheckConstraint(
            "producto_id IS NOT NULL OR categoria_id IS NOT NULL", name="ck_tabla_medida_producto_o_categoria"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    producto_id: Mapped[int | None] = mapped_column(ForeignKey("producto.id", ondelete="CASCADE"))
    categoria_id: Mapped[int | None] = mapped_column(ForeignKey("categoria.id"))
    talla_id: Mapped[int] = mapped_column(ForeignKey("talla.id"), nullable=False)
    pecho_min_cm: Mapped[Decimal | None] = mapped_column(Numeric(5, 1))
    pecho_max_cm: Mapped[Decimal | None] = mapped_column(Numeric(5, 1))
    cintura_min_cm: Mapped[Decimal | None] = mapped_column(Numeric(5, 1))
    cintura_max_cm: Mapped[Decimal | None] = mapped_column(Numeric(5, 1))
    hombros_cm: Mapped[Decimal | None] = mapped_column(Numeric(5, 1))
    largo_cm: Mapped[Decimal | None] = mapped_column(Numeric(5, 1))
