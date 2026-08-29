from __future__ import annotations

import datetime as dt
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

TipoActivo = Literal["overlay_2d", "flatlay_ia", "thumb"]
EstadoActivo = Literal["pendiente", "validado", "rechazado"]


class Ancla(BaseModel):
    x: float = Field(ge=0, le=1)
    y: float = Field(ge=0, le=1)


class AnclajesActualizar(BaseModel):
    hombro_izq: Ancla
    hombro_der: Ancla
    cadera: Ancla


class ActivoRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    variante_id: int
    tipo: str
    public_id: str
    url: str
    anclajes: dict | None = None
    ancho_px: int | None = None
    alto_px: int | None = None
    estado: str
    creado_en: dt.datetime

    @classmethod
    def from_modelo(cls, activo, url: str) -> "ActivoRespuesta":
        return cls(
            id=activo.id,
            variante_id=activo.variante_id,
            tipo=activo.tipo,
            public_id=activo.url,
            url=url,
            anclajes=activo.anclajes,
            ancho_px=activo.ancho_px,
            alto_px=activo.alto_px,
            estado=activo.estado,
            creado_en=activo.creado_en,
        )
