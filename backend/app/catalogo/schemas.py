from __future__ import annotations

import datetime as dt

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
