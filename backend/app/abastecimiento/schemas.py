from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

EstadoOrdenCompra = Literal["borrador", "enviada", "parcial", "recibida", "anulada"]

# ---- Proveedor ----------------------------------------------------------------


class ProveedorCrear(BaseModel):
    nombre: str = Field(max_length=120)
    nit: str | None = Field(default=None, max_length=20)
    contacto: str | None = Field(default=None, max_length=80)
    telefono: str | None = Field(default=None, max_length=20)
    email: str | None = Field(default=None, max_length=120)
    direccion: str | None = Field(default=None, max_length=200)
    usuario_id: int | None = None


class ProveedorActualizar(BaseModel):
    nombre: str | None = Field(default=None, max_length=120)
    nit: str | None = Field(default=None, max_length=20)
    contacto: str | None = Field(default=None, max_length=80)
    telefono: str | None = Field(default=None, max_length=20)
    email: str | None = Field(default=None, max_length=120)
    direccion: str | None = Field(default=None, max_length=200)
    usuario_id: int | None = None
    activo: bool | None = None


class ProveedorRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    nit: str | None
    contacto: str | None
    telefono: str | None
    email: str | None
    direccion: str | None
    usuario_id: int | None
    activo: bool
    creado_en: dt.datetime


# ---- Producto-proveedor ---------------------------------------------------------


class ProductoProveedorCrear(BaseModel):
    producto_id: int
    costo_referencial: Decimal | None = Field(default=None, ge=0)
    dias_entrega: int | None = Field(default=None, ge=0)


class ProductoProveedorRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    proveedor_id: int
    producto_id: int
    costo_referencial: Decimal | None
    dias_entrega: int | None


# ---- Orden de compra ------------------------------------------------------------


class OrdenCompraDetalleCrear(BaseModel):
    variante_id: int
    cantidad: int = Field(gt=0)
    costo_unitario: Decimal = Field(ge=0)


class OrdenCompraDetalleRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    variante_id: int
    cantidad: int
    costo_unitario: Decimal


class OrdenCompraCrear(BaseModel):
    codigo: str = Field(max_length=20)
    proveedor_id: int
    sucursal_id: int
    fecha_esperada: dt.date | None = None
    detalle: list[OrdenCompraDetalleCrear] = Field(min_length=1)


class OrdenCompraActualizar(BaseModel):
    """Solo se puede editar mientras la orden está en 'borrador'. Si viene
    `detalle`, reemplaza la lista completa (no hace merge línea por línea)."""

    proveedor_id: int | None = None
    sucursal_id: int | None = None
    fecha_esperada: dt.date | None = None
    detalle: list[OrdenCompraDetalleCrear] | None = Field(default=None, min_length=1)


class OrdenCompraRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
    proveedor_id: int
    sucursal_id: int
    fecha_emision: dt.date
    fecha_esperada: dt.date | None
    estado: EstadoOrdenCompra
    total: Decimal
    creado_por: int | None
    creado_en: dt.datetime
    detalle: list[OrdenCompraDetalleRespuesta]


# ---- Recepción --------------------------------------------------------------------


class RecepcionDetalleCrear(BaseModel):
    variante_id: int
    cantidad: int = Field(gt=0)
    costo_unitario: Decimal = Field(ge=0)


class RecepcionDetalleRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    variante_id: int
    cantidad: int
    costo_unitario: Decimal


class RecepcionCrear(BaseModel):
    codigo: str = Field(max_length=20)
    orden_compra_id: int | None = None
    proveedor_id: int
    sucursal_id: int
    empleado_id: int | None = None
    observacion: str | None = Field(default=None, max_length=300)
    detalle: list[RecepcionDetalleCrear] = Field(min_length=1)


class RecepcionRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
    orden_compra_id: int | None
    proveedor_id: int
    sucursal_id: int
    empleado_id: int | None
    fecha: dt.datetime
    observacion: str | None
    detalle: list[RecepcionDetalleRespuesta]
