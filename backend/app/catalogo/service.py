from sqlalchemy.orm import Session

from app.core.exceptions import ConflictoError, DomainError, NoEncontradoError
from app.catalogo.models import Categoria, Coleccion, Temporada
from app.catalogo.repository import (
    CategoriaRepository,
    ColeccionRepository,
    TemporadaRepository,
)
from app.catalogo.schemas import (
    CategoriaActualizar,
    CategoriaCrear,
    ColeccionActualizar,
    ColeccionCrear,
    TemporadaActualizar,
)

categoria_repo = CategoriaRepository()
temporada_repo = TemporadaRepository()
coleccion_repo = ColeccionRepository()


def _crearia_ciclo(db: Session, categoria_id: int, nuevo_padre_id: int) -> bool:
    """True si engancharle `nuevo_padre_id` como padre de `categoria_id`
    crea un ciclo (incluye el caso trivial de ser su propio padre)."""
    actual: int | None = nuevo_padre_id
    visitados: set[int] = set()
    while actual is not None:
        if actual == categoria_id:
            return True
        if actual in visitados:
            break
        visitados.add(actual)
        padre = db.get(Categoria, actual)
        actual = padre.categoria_padre_id if padre else None
    return False


def _validar_padre(db: Session, categoria_id: int | None, categoria_padre_id: int | None) -> None:
    if categoria_padre_id is None:
        return
    padre = db.get(Categoria, categoria_padre_id)
    if padre is None or not padre.activo:
        raise NoEncontradoError("Categoría padre no encontrada")
    if categoria_id is not None and _crearia_ciclo(db, categoria_id, categoria_padre_id):
        raise DomainError("Una categoría no puede ser su propio padre ni crear un ciclo")


def crear_categoria(db: Session, datos: CategoriaCrear) -> Categoria:
    _validar_padre(db, None, datos.categoria_padre_id)
    return categoria_repo.crear(db, datos)


def actualizar_categoria(db: Session, categoria_id: int, datos: CategoriaActualizar) -> Categoria:
    if datos.categoria_padre_id is not None:
        _validar_padre(db, categoria_id, datos.categoria_padre_id)
    return categoria_repo.actualizar(db, categoria_id, datos)


def desactivar_categoria(db: Session, categoria_id: int) -> Categoria:
    if categoria_repo.listar_hijos(db, categoria_id):
        raise ConflictoError("No se puede desactivar: la categoría tiene subcategorías activas")
    # TODO(P2.2): bloquear también si hay productos asociados, cuando
    # exista el paquete de productos.
    return categoria_repo.desactivar(db, categoria_id)


def actualizar_temporada(db: Session, temporada_id: int, datos: TemporadaActualizar) -> Temporada:
    temporada = temporada_repo.obtener(db, temporada_id)
    inicio = datos.fecha_inicio if "fecha_inicio" in datos.model_fields_set else temporada.fecha_inicio
    fin = datos.fecha_fin if "fecha_fin" in datos.model_fields_set else temporada.fecha_fin
    if inicio and fin and fin <= inicio:
        raise DomainError("fecha_fin debe ser posterior a fecha_inicio")
    return temporada_repo.actualizar(db, temporada_id, datos)


def crear_coleccion(db: Session, datos: ColeccionCrear) -> Coleccion:
    if datos.temporada_id is not None:
        temporada_repo.obtener(db, datos.temporada_id)
    return coleccion_repo.crear(db, datos)


def actualizar_coleccion(db: Session, coleccion_id: int, datos: ColeccionActualizar) -> Coleccion:
    if datos.temporada_id is not None:
        temporada_repo.obtener(db, datos.temporada_id)
    return coleccion_repo.actualizar(db, coleccion_id, datos)
