"""Almacenamiento de imágenes en Cloudinary.

Todo el flujo pasa por el backend: el cliente nunca sube directo a
Cloudinary ni recibe ninguna credencial. `cloudinary.config()` guarda el
api_secret en memoria del proceso del servidor; ningún schema de
respuesta ni el bundle del front lo tocan.

Convención del proyecto: en la base de datos se guarda el `public_id` de
Cloudinary, nunca la URL completa (la columna `producto_imagen.url` del
esquema, pese al nombre, guarda el public_id — la URL se genera al vuelo
con las funciones de acá abajo, así se puede cambiar de transformación sin
tocar filas existentes).
"""

from __future__ import annotations

import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url

from app.core.config import get_settings

settings = get_settings()

cloudinary.config(
    cloud_name=settings.cloudinary_cloud_name,
    api_key=settings.cloudinary_api_key,
    api_secret=settings.cloudinary_api_secret,
    secure=True,
)


def carpeta_producto(producto_id: int) -> str:
    return f"fashionstore/productos/{producto_id}"


def carpeta_probador(variante_id: int) -> str:
    return f"fashionstore/probador/{variante_id}"


def carpeta_probador_generado(variante_id: int) -> str:
    return f"fashionstore/probador/{variante_id}/generado"


def subir_imagen(contenido: bytes, carpeta: str, *, formato_forzado: str | None = None) -> str:
    """Sube un archivo a Cloudinary y devuelve su `public_id`.

    `formato_forzado="png"` se usa para los assets del probador: hay que
    preservar el canal alfa, así que nunca se deja que Cloudinary elija
    el formato de salida (eso es lo que hace f_auto, y lo tira a JPEG).
    """
    opciones: dict = {"folder": carpeta, "resource_type": "image", "unique_filename": True, "overwrite": False}
    if formato_forzado:
        opciones["format"] = formato_forzado
    resultado = cloudinary.uploader.upload(contenido, **opciones)
    return resultado["public_id"]


def eliminar_imagen(public_id: str) -> None:
    cloudinary.uploader.destroy(public_id)


def url_catalogo(public_id: str, ancho: int | None = None, alto: int | None = None) -> str:
    """URL para imágenes de catálogo: f_auto + q_auto (Cloudinary elige el
    mejor formato y calidad según quién pide la imagen)."""
    transformacion: dict = {"fetch_format": "auto", "quality": "auto"}
    if ancho is not None:
        transformacion["width"] = ancho
    if alto is not None:
        transformacion["height"] = alto
    if ancho is not None or alto is not None:
        transformacion["crop"] = "limit"
    url, _ = cloudinary_url(public_id, secure=True, **transformacion)
    return url


def url_probador(public_id: str) -> str:
    """URL para los PNG del probador: SIN f_auto. El formato se fuerza a
    png para no perder el canal alfa (f_auto podría devolver JPEG)."""
    url, _ = cloudinary_url(public_id, secure=True, format="png")
    return url
