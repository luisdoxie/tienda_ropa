"""Cliente del parser de voz vía Groq.

Todo lo que sabe llamar al proveedor externo que interpreta la frase
transcrita vive detrás de `ParserVozBase`. El resto del paquete
(`service.py`) solo conoce esta interfaz, nunca al proveedor concreto --
mismo patrón que `probador/generativo.py` usa para Vertex AI.
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod

import httpx
from pydantic import ValidationError

from app.catalogo.schemas import ValoresReferenciaCatalogo
from app.core.config import get_settings
from app.inteligencia.schemas import FiltrosVoz

logger = logging.getLogger(__name__)

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
TIMEOUT_SEG = 10


def _armar_prompt(valores: ValoresReferenciaCatalogo) -> str:
    return (
        "Sos el intérprete de búsqueda por voz de una tienda de ropa. A partir "
        "de la frase del usuario, devolvé ÚNICAMENTE un JSON con esta forma "
        "exacta, sin texto adicional ni markdown:\n"
        '{"categoria": null, "temporada": null, "material": null, "color": null, '
        '"talla": null, "genero": null, "precio_max": null, "sucursal": null}\n\n'
        "Reglas:\n"
        "- Cada valor debe ser uno de los valores válidos listados abajo, o null "
        "si la frase no lo menciona o ninguno corresponde. Mapeá sinónimos al "
        'valor real más parecido (ej. "hilo" -> el material más parecido de la '
        "lista).\n"
        f"- categoria: uno de {valores.categorias}\n"
        f"- material: uno de {valores.materiales}\n"
        f"- color: uno de {valores.colores}\n"
        f"- talla: uno de {valores.tallas}\n"
        f"- temporada: uno de {valores.temporadas}\n"
        '- genero: uno de ["hombre", "mujer", "unisex", "nino"]\n'
        "- precio_max: un número (el precio máximo que menciona la frase, sin "
        "moneda), o null\n"
        "- sucursal: el nombre de una sucursal si la frase la menciona "
        "explícitamente, o null"
    )


class ParserVozBase(ABC):
    nombre: str

    @abstractmethod
    def parsear(self, texto: str, valores: ValoresReferenciaCatalogo) -> FiltrosVoz | None:
        """Devuelve los filtros interpretados, o `None` si el proveedor
        falló o su respuesta no se pudo validar -- nunca lanza excepción,
        el llamador decide el fallback a búsqueda de texto plano."""
        raise NotImplementedError


class GroqParserVoz(ParserVozBase):
    nombre = "groq"

    def __init__(self) -> None:
        settings = get_settings()
        self._api_key = settings.groq_api_key
        self._modelo = settings.groq_modelo

    def parsear(self, texto: str, valores: ValoresReferenciaCatalogo) -> FiltrosVoz | None:
        if not self._api_key:
            logger.warning("GROQ_API_KEY no configurado, se usa fallback de texto plano")
            return None
        try:
            respuesta = httpx.post(
                GROQ_URL,
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "model": self._modelo,
                    "messages": [
                        {"role": "system", "content": _armar_prompt(valores)},
                        {"role": "user", "content": texto},
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0,
                },
                timeout=TIMEOUT_SEG,
            )
            respuesta.raise_for_status()
            contenido = respuesta.json()["choices"][0]["message"]["content"]
            return FiltrosVoz.model_validate(json.loads(contenido))
        except (httpx.HTTPError, KeyError, IndexError, ValueError, ValidationError):
            # Cualquier falla del proveedor externo (red, formato de la
            # respuesta, JSON inválido, o JSON válido que no matchea
            # FiltrosVoz) cae al fallback -- nunca se propaga al request.
            logger.exception("Groq falló al interpretar la búsqueda por voz, se usa fallback de texto plano")
            return None


def obtener_parser_voz() -> ParserVozBase:
    return GroqParserVoz()
