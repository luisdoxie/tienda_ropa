import io

from PIL import Image, UnidentifiedImageError
from sqlalchemy.orm import Session

from app.core import storage
from app.core.exceptions import DomainError
from app.catalogo import service as catalogo_service
from app.probador.models import ActivoProbador
from app.probador.repository import ActivoRepository
from app.probador.schemas import AnclajesActualizar

activo_repo = ActivoRepository()

TIPOS_VALIDOS = {"overlay_2d", "flatlay_ia", "thumb"}
LADO_MINIMO_PX = 512
TAMANIO_MAXIMO_BYTES = 3 * 1024 * 1024  # 3MB


def _validar_png_con_alfa(contenido: bytes) -> tuple[int, int]:
    """Abre el archivo con Pillow (no confía en la extensión ni en el
    content-type que mandó el cliente) y confirma que sea un PNG real con
    canal alfa, y que cumpla el tamaño mínimo/máximo."""
    if len(contenido) > TAMANIO_MAXIMO_BYTES:
        raise DomainError("El archivo supera el tamaño máximo permitido (3MB)")

    try:
        imagen = Image.open(io.BytesIO(contenido))
        imagen.load()
    except UnidentifiedImageError as exc:
        raise DomainError("El archivo no es una imagen válida") from exc

    if imagen.format != "PNG":
        raise DomainError("El archivo debe ser un PNG")

    tiene_alfa = imagen.mode in ("RGBA", "LA") or "transparency" in imagen.info
    if not tiene_alfa:
        raise DomainError("El PNG debe tener canal alfa real")

    ancho, alto = imagen.size
    if ancho < LADO_MINIMO_PX or alto < LADO_MINIMO_PX:
        raise DomainError(f"La imagen debe medir al menos {LADO_MINIMO_PX}px de lado")

    return ancho, alto


def subir_asset(
    db: Session,
    variante_id: int,
    tipo: str,
    contenido: bytes,
    content_type: str | None,
    creado_por: int | None,
) -> tuple[ActivoProbador, str]:
    catalogo_service.obtener_variante(db, variante_id)  # 404 si no existe

    if tipo not in TIPOS_VALIDOS:
        raise DomainError(f"tipo debe ser uno de {sorted(TIPOS_VALIDOS)}")
    if content_type != "image/png":
        raise DomainError("El archivo debe subirse como image/png")

    ancho, alto = _validar_png_con_alfa(contenido)

    # Nunca f_auto acá: hay que preservar el canal alfa (ver core/storage.py).
    public_id = storage.subir_imagen(
        contenido, storage.carpeta_probador(variante_id), formato_forzado="png"
    )

    activo = activo_repo.crear(db, variante_id, tipo, public_id, ancho, alto, creado_por)
    return activo, storage.url_probador(public_id)


def guardar_anclajes(db: Session, activo_id: int, datos: AnclajesActualizar) -> tuple[ActivoProbador, str]:
    activo = activo_repo.obtener(db, activo_id)
    activo = activo_repo.guardar_anclajes(db, activo, datos.model_dump())
    return activo, storage.url_probador(activo.url)


def validar_asset(db: Session, activo_id: int) -> tuple[ActivoProbador, str]:
    activo = activo_repo.obtener(db, activo_id)
    if activo.estado != "pendiente":
        raise DomainError(f"El asset ya está en estado '{activo.estado}'")
    if not activo.anclajes:
        raise DomainError("No se puede validar un asset sin anclajes")
    activo = activo_repo.marcar_validado(db, activo)
    return activo, storage.url_probador(activo.url)


def listar_assets(db: Session, variante_id: int) -> list[tuple[ActivoProbador, str]]:
    catalogo_service.obtener_variante(db, variante_id)  # 404 si no existe
    activos = activo_repo.listar_por_variante(db, variante_id)
    return [(a, storage.url_probador(a.url)) for a in activos]
