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


class AssetsVarianteRespuesta(BaseModel):
    """Lo que necesita el modo espejo en Flutter para una variante:
    el overlay validado (obligatorio para probar) y el flat-lay
    generado, si algún admin ya lo subió y validó."""

    overlay: ActivoRespuesta
    flatlay: ActivoRespuesta | None = None


EstadoGeneracion = Literal["en_proceso", "completado", "fallido"]


class GeneracionIniciadaRespuesta(BaseModel):
    id: int
    estado: EstadoGeneracion
    url_resultado: str | None = None
    desde_cache: bool


class GeneracionEstadoRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    estado: EstadoGeneracion
    url_resultado: str | None = None
    mensaje_error: str | None = None


ModoProbador = Literal["espejo", "generativo"]


class SesionCrear(BaseModel):
    variante_id: int
    modo: ModoProbador
    duracion_seg: int | None = Field(default=None, ge=0)


class SesionRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    variante_id: int
    modo: ModoProbador
    duracion_seg: int | None = None
    creado_en: dt.datetime


PreferenciaAjuste = Literal["ajustado", "regular", "holgado"]


class TallaRequest(BaseModel):
    variante_id: int
    estatura_cm: float = Field(ge=100, le=230)
    peso_kg: float = Field(ge=30, le=250)
    preferencia_ajuste: PreferenciaAjuste = "regular"


class TallaRecomendadaRespuesta(BaseModel):
    talla_id: int | None
    talla_codigo: str | None
    pecho_estimado_cm: float
    cintura_estimado_cm: float
    advertencia: str | None = None
