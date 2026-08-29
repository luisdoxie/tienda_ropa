from __future__ import annotations

import datetime as dt
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

EstadoReservaCodigo = Literal["pendiente", "preparada", "en_prueba", "completada", "cancelada", "expirada"]

# ---- Crear -------------------------------------------------------------------


class ReservaDetalleCrear(BaseModel):
    variante_id: int
    cantidad: int = Field(default=1, gt=0)


class ReservaCrear(BaseModel):
    sucursal_id: int
    fecha_visita: dt.date
    hora_visita_desde: dt.time
    hora_visita_hasta: dt.time
    observacion: str | None = Field(default=None, max_length=300)
    detalle: list[ReservaDetalleCrear] = Field(min_length=1)


# ---- Selección -----------------------------------------------------------------


class SeleccionLinea(BaseModel):
    variante_id: int
    seleccionada: bool


class SeleccionActualizar(BaseModel):
    lineas: list[SeleccionLinea] = Field(min_length=1)


# ---- Respuestas ----------------------------------------------------------------


class ReservaDetalleRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    variante_id: int
    cantidad: int
    seleccionada: bool | None
    preparada: bool


class ReservaHistorialRespuesta(BaseModel):
    id: int
    estado: str
    usuario_id: int | None
    comentario: str | None
    creado_en: dt.datetime


class ReservaRespuesta(BaseModel):
    id: int
    codigo: str
    cliente_id: int
    sucursal_id: int
    estado: EstadoReservaCodigo
    fecha_visita: dt.date
    hora_visita_desde: dt.time
    hora_visita_hasta: dt.time
    fecha_expiracion: dt.datetime
    observacion: str | None
    creado_en: dt.datetime
    detalle: list[ReservaDetalleRespuesta]
    historial: list[ReservaHistorialRespuesta]

    @classmethod
    def from_modelo(cls, reserva, estados_por_id: dict[int, str]) -> "ReservaRespuesta":
        return cls(
            id=reserva.id,
            codigo=reserva.codigo,
            cliente_id=reserva.cliente_id,
            sucursal_id=reserva.sucursal_id,
            estado=estados_por_id[reserva.estado_id],
            fecha_visita=reserva.fecha_visita,
            hora_visita_desde=reserva.hora_visita_desde,
            hora_visita_hasta=reserva.hora_visita_hasta,
            fecha_expiracion=reserva.fecha_expiracion,
            observacion=reserva.observacion,
            creado_en=reserva.creado_en,
            detalle=[ReservaDetalleRespuesta.model_validate(d) for d in reserva.detalle],
            historial=[
                ReservaHistorialRespuesta(
                    id=h.id,
                    estado=estados_por_id[h.estado_id],
                    usuario_id=h.usuario_id,
                    comentario=h.comentario,
                    creado_en=h.creado_en,
                )
                for h in reserva.historial
            ],
        )
