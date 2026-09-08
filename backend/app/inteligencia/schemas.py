from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field

from app.catalogo.schemas import CatalogoItemRespuesta, FiltrosCatalogo

# Los únicos valores que catalogo.schemas.Genero acepta. FiltrosVoz recibe el
# género tal cual lo devuelve Groq (str libre, no el Literal), porque un
# valor fuera de esta lista no debe tirar abajo la validación de todo el
# JSON -- se descarta ese campo puntual en el service, no la respuesta entera.
GENEROS_VALIDOS = {"hombre", "mujer", "unisex", "nino"}


class VozRequest(BaseModel):
    texto: str = Field(min_length=1, max_length=300)


class FiltrosVoz(BaseModel):
    """Contrato exacto que debe devolver Groq (P6.1): un JSON con estas
    ocho claves, sin texto adicional ni markdown. Todo opcional -- Groq
    manda `null` en lo que la frase no menciona."""

    categoria: str | None = None
    temporada: str | None = None
    material: str | None = None
    color: str | None = None
    talla: str | None = None
    genero: str | None = None
    precio_max: Decimal | None = None
    sucursal: str | None = None


class VozRespuesta(BaseModel):
    resultados: list[CatalogoItemRespuesta]
    filtros: FiltrosCatalogo
    etiquetas: dict[str, str]
    cantidad: int
