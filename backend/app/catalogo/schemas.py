from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

# ---- Categoría ------------------------------------------------------------


class CategoriaCrear(BaseModel):
    nombre: str = Field(max_length=60)
    descripcion: str | None = Field(default=None, max_length=200)
    categoria_padre_id: int | None = None


class CategoriaActualizar(BaseModel):
    nombre: str | None = Field(default=None, max_length=60)
    descripcion: str | None = Field(default=None, max_length=200)
    categoria_padre_id: int | None = None


class CategoriaRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    categoria_padre_id: int | None = None
    nombre: str
    descripcion: str | None = None
    activo: bool


# ---- Talla -----------------------------------------------------------------


class TallaCrear(BaseModel):
    codigo: str = Field(max_length=10)
    descripcion: str | None = Field(default=None, max_length=40)
    orden: int = 0


class TallaActualizar(BaseModel):
    codigo: str | None = Field(default=None, max_length=10)
    descripcion: str | None = Field(default=None, max_length=40)
    orden: int | None = None


class TallaRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
    descripcion: str | None = None
    orden: int


# ---- Color -----------------------------------------------------------------


class ColorCrear(BaseModel):
    nombre: str = Field(max_length=40)
    codigo_hex: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")


class ColorActualizar(BaseModel):
    nombre: str | None = Field(default=None, max_length=40)
    codigo_hex: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")


class ColorRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    codigo_hex: str | None = None


# ---- Material ----------------------------------------------------------------


class MaterialCrear(BaseModel):
    nombre: str = Field(max_length=40)
    descripcion: str | None = Field(default=None, max_length=200)


class MaterialActualizar(BaseModel):
    nombre: str | None = Field(default=None, max_length=40)
    descripcion: str | None = Field(default=None, max_length=200)


class MaterialRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    descripcion: str | None = None


# ---- Temporada ---------------------------------------------------------------


class TemporadaCrear(BaseModel):
    nombre: str = Field(max_length=60)
    anio: int = Field(ge=2000, le=2100)
    fecha_inicio: dt.date | None = None
    fecha_fin: dt.date | None = None

    @model_validator(mode="after")
    def _validar_rango(self) -> "TemporadaCrear":
        if self.fecha_inicio and self.fecha_fin and self.fecha_fin <= self.fecha_inicio:
            raise ValueError("fecha_fin debe ser posterior a fecha_inicio")
        return self


class TemporadaActualizar(BaseModel):
    nombre: str | None = Field(default=None, max_length=60)
    anio: int | None = Field(default=None, ge=2000, le=2100)
    fecha_inicio: dt.date | None = None
    fecha_fin: dt.date | None = None
    activo: bool | None = None

    @model_validator(mode="after")
    def _validar_rango(self) -> "TemporadaActualizar":
        if self.fecha_inicio and self.fecha_fin and self.fecha_fin <= self.fecha_inicio:
            raise ValueError("fecha_fin debe ser posterior a fecha_inicio")
        return self


class TemporadaRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    anio: int
    fecha_inicio: dt.date | None = None
    fecha_fin: dt.date | None = None
    activo: bool


# ---- Colección ---------------------------------------------------------------


class ColeccionCrear(BaseModel):
    temporada_id: int | None = None
    nombre: str = Field(max_length=80)
    descripcion: str | None = Field(default=None, max_length=300)


class ColeccionActualizar(BaseModel):
    temporada_id: int | None = None
    nombre: str | None = Field(default=None, max_length=80)
    descripcion: str | None = Field(default=None, max_length=300)
    activo: bool | None = None


class ColeccionRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    temporada_id: int | None = None
    nombre: str
    descripcion: str | None = None
    activo: bool


Genero = Literal["hombre", "mujer", "unisex", "nino"]

# ---- Producto ---------------------------------------------------------------


class ProductoCrear(BaseModel):
    codigo: str = Field(max_length=30)
    nombre: str = Field(max_length=120)
    descripcion: str | None = None
    categoria_id: int
    material_id: int | None = None
    temporada_id: int | None = None
    coleccion_id: int | None = None
    genero: Genero = "unisex"
    precio_base: Decimal = Field(ge=0)
    admite_probador: bool = False
    tallas_ids: list[int] = Field(min_length=1)
    colores_ids: list[int] = Field(min_length=1)


class ProductoActualizar(BaseModel):
    codigo: str | None = Field(default=None, max_length=30)
    nombre: str | None = Field(default=None, max_length=120)
    descripcion: str | None = None
    categoria_id: int | None = None
    material_id: int | None = None
    temporada_id: int | None = None
    coleccion_id: int | None = None
    genero: Genero | None = None
    precio_base: Decimal | None = Field(default=None, ge=0)
    admite_probador: bool | None = None
    activo: bool | None = None


class ProductoRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
    nombre: str
    descripcion: str | None = None
    categoria_id: int
    material_id: int | None = None
    temporada_id: int | None = None
    coleccion_id: int | None = None
    genero: str
    precio_base: Decimal
    admite_probador: bool
    activo: bool
    creado_en: dt.datetime
    creado_por: int | None = None


# ---- Variantes ---------------------------------------------------------------


class VariantesGenerarRequest(BaseModel):
    """Agrega nuevas tallas/colores a un producto ya creado. La
    combinatoria que ya existe no se toca ni se duplica."""

    tallas_ids: list[int] = Field(min_length=1)
    colores_ids: list[int] = Field(min_length=1)


class VarianteActualizar(BaseModel):
    precio: Decimal | None = Field(default=None, ge=0)
    activo: bool | None = None


class VarianteRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    producto_id: int
    talla_id: int
    color_id: int
    sku: str
    codigo_barras: str | None = None
    precio: Decimal | None = None
    precio_efectivo: Decimal
    activo: bool

    @classmethod
    def from_modelo(cls, variante) -> "VarianteRespuesta":
        return cls(
            id=variante.id,
            producto_id=variante.producto_id,
            talla_id=variante.talla_id,
            color_id=variante.color_id,
            sku=variante.sku,
            codigo_barras=variante.codigo_barras,
            precio=variante.precio,
            precio_efectivo=variante.precio if variante.precio is not None else variante.producto.precio_base,
            activo=variante.activo,
        )


# ---- Tabla de medidas ---------------------------------------------------------


class TablaMedidaCrear(BaseModel):
    talla_id: int
    pecho_min_cm: Decimal | None = None
    pecho_max_cm: Decimal | None = None
    cintura_min_cm: Decimal | None = None
    cintura_max_cm: Decimal | None = None
    hombros_cm: Decimal | None = None
    largo_cm: Decimal | None = None


class TablaMedidaActualizar(BaseModel):
    talla_id: int | None = None
    pecho_min_cm: Decimal | None = None
    pecho_max_cm: Decimal | None = None
    cintura_min_cm: Decimal | None = None
    cintura_max_cm: Decimal | None = None
    hombros_cm: Decimal | None = None
    largo_cm: Decimal | None = None


class TablaMedidaRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    producto_id: int | None = None
    categoria_id: int | None = None
    talla_id: int
    pecho_min_cm: Decimal | None = None
    pecho_max_cm: Decimal | None = None
    cintura_min_cm: Decimal | None = None
    cintura_max_cm: Decimal | None = None
    hombros_cm: Decimal | None = None
    largo_cm: Decimal | None = None
