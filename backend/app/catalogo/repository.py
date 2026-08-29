from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.crud_base import CRUDBase, CRUDBaseSinActivo
from app.core.exceptions import ConflictoError
from app.catalogo.models import Categoria, Coleccion, Color, Material, Talla, Temporada
from app.catalogo.schemas import (
    CategoriaActualizar,
    CategoriaCrear,
    ColeccionActualizar,
    ColeccionCrear,
    ColorActualizar,
    ColorCrear,
    MaterialActualizar,
    MaterialCrear,
    TallaActualizar,
    TallaCrear,
    TemporadaActualizar,
    TemporadaCrear,
)


class CategoriaRepository(CRUDBase[Categoria, CategoriaCrear, CategoriaActualizar]):
    def __init__(self) -> None:
        super().__init__(Categoria)

    def listar_hijos(self, db: Session, categoria_id: int) -> list[Categoria]:
        return list(
            db.scalars(
                select(Categoria).where(
                    Categoria.categoria_padre_id == categoria_id, Categoria.activo.is_(True)
                )
            )
        )


class TallaRepository(CRUDBaseSinActivo[Talla, TallaCrear, TallaActualizar]):
    def __init__(self) -> None:
        super().__init__(Talla)

    def listar(self, db, paginacion, filtros=None):
        consulta = select(Talla).order_by(Talla.orden).offset(paginacion.offset).limit(paginacion.tamanio)
        return list(db.scalars(consulta).all())

    def obtener_por_codigo(self, db: Session, codigo: str) -> Talla | None:
        return db.scalar(select(Talla).where(Talla.codigo == codigo))

    def crear(self, db: Session, datos: TallaCrear) -> Talla:
        if self.obtener_por_codigo(db, datos.codigo) is not None:
            raise ConflictoError("Ya existe una talla con ese código")
        return super().crear(db, datos)

    def actualizar(self, db: Session, id_: int, datos: TallaActualizar) -> Talla:
        if datos.codigo is not None:
            existente = self.obtener_por_codigo(db, datos.codigo)
            if existente is not None and existente.id != id_:
                raise ConflictoError("Ya existe una talla con ese código")
        return super().actualizar(db, id_, datos)


class ColorRepository(CRUDBaseSinActivo[Color, ColorCrear, ColorActualizar]):
    def __init__(self) -> None:
        super().__init__(Color)


class MaterialRepository(CRUDBaseSinActivo[Material, MaterialCrear, MaterialActualizar]):
    def __init__(self) -> None:
        super().__init__(Material)


class TemporadaRepository(CRUDBase[Temporada, TemporadaCrear, TemporadaActualizar]):
    def __init__(self) -> None:
        super().__init__(Temporada)

    def _existe_duplicada(self, db: Session, nombre: str, anio: int, excluir_id: int | None = None) -> bool:
        consulta = select(Temporada).where(Temporada.nombre == nombre, Temporada.anio == anio)
        if excluir_id is not None:
            consulta = consulta.where(Temporada.id != excluir_id)
        return db.scalar(consulta) is not None

    def crear(self, db: Session, datos: TemporadaCrear) -> Temporada:
        if self._existe_duplicada(db, datos.nombre, datos.anio):
            raise ConflictoError("Ya existe una temporada con ese nombre y año")
        return super().crear(db, datos)

    def actualizar(self, db: Session, id_: int, datos: TemporadaActualizar) -> Temporada:
        if datos.nombre is not None or datos.anio is not None:
            actual = self.obtener(db, id_)
            nombre = datos.nombre if datos.nombre is not None else actual.nombre
            anio = datos.anio if datos.anio is not None else actual.anio
            if self._existe_duplicada(db, nombre, anio, excluir_id=id_):
                raise ConflictoError("Ya existe una temporada con ese nombre y año")
        return super().actualizar(db, id_, datos)


class ColeccionRepository(CRUDBase[Coleccion, ColeccionCrear, ColeccionActualizar]):
    def __init__(self) -> None:
        super().__init__(Coleccion)
