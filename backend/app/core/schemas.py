from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict


class NotificacionRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    titulo: str
    mensaje: str | None
    tipo: str | None
    referencia_id: int | None
    leida: bool
    creado_en: dt.datetime
