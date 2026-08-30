from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

EstadoEnvio = Literal["programado", "en_ruta", "entregado", "fallido"]


# ---- Zonas de envío ---------------------------------------------------------


class ZonaEnvioCrear(BaseModel):
    ciudad_id: int
    nombre: str = Field(max_length=60)
    anillo_desde: int | None = Field(default=None, ge=1)
    anillo_hasta: int | None = Field(default=None, ge=1)
    tarifa_base: Decimal = Field(ge=0)


class ZonaEnvioActualizar(BaseModel):
    nombre: str | None = Field(default=None, max_length=60)
    anillo_desde: int | None = Field(default=None, ge=1)
    anillo_hasta: int | None = Field(default=None, ge=1)
    tarifa_base: Decimal | None = Field(default=None, ge=0)
    activo: bool | None = None


class ZonaEnvioRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ciudad_id: int
    nombre: str
    anillo_desde: int | None = None
    anillo_hasta: int | None = None
    tarifa_base: Decimal
    activo: bool


# ---- Direcciones de cliente ---------------------------------------------------
# Sin cliente_id en el Crear: se resuelve del usuario autenticado en el
# service, igual que carrito (nunca se confía en un cliente_id del body).


class DireccionClienteCrear(BaseModel):
    zona_envio_id: int | None = None
    alias: str | None = Field(default=None, max_length=40)
    direccion: str = Field(max_length=200)
    referencia: str | None = Field(default=None, max_length=200)
    latitud: Decimal | None = None
    longitud: Decimal | None = None
    es_principal: bool = False


class DireccionClienteActualizar(BaseModel):
    zona_envio_id: int | None = None
    alias: str | None = Field(default=None, max_length=40)
    direccion: str | None = Field(default=None, max_length=200)
    referencia: str | None = Field(default=None, max_length=200)
    latitud: Decimal | None = None
    longitud: Decimal | None = None
    es_principal: bool | None = None
    activo: bool | None = None


class DireccionClienteRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cliente_id: int
    zona_envio_id: int | None = None
    alias: str | None = None
    direccion: str
    referencia: str | None = None
    latitud: Decimal | None = None
    longitud: Decimal | None = None
    es_principal: bool
    activo: bool


# ---- Cotización (no persiste) y envíos -----------------------------------------


class CotizarEnvioRequest(BaseModel):
    direccion_id: int
    cantidad_prendas: int = Field(gt=0)


class CotizarEnvioRespuesta(BaseModel):
    zona_envio_id: int
    zona_nombre: str
    peso_kg: Decimal
    tarifa_base: Decimal
    recargo_peso: Decimal
    costo: Decimal


class EnvioCrear(BaseModel):
    venta_id: int
    direccion_id: int


class EnvioRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    venta_id: int
    direccion_id: int
    zona_envio_id: int
    costo: Decimal
    peso_kg: Decimal | None = None
    estado: EstadoEnvio
    fecha_programada: dt.datetime | None = None
    fecha_entrega: dt.datetime | None = None
    repartidor: str | None = None


class EnvioEstadoActualizar(BaseModel):
    estado: EstadoEnvio
    repartidor: str | None = Field(default=None, max_length=80)
