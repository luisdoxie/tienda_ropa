from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.crud_base import CRUDBase, CRUDBaseSinActivo
from app.core.exceptions import ConflictoError, NoEncontradoError
from app.catalogo.models import (
    Categoria,
    Coleccion,
    Color,
    Material,
    Producto,
    ProductoVariante,
    Talla,
    TablaMedida,
    Temporada,
)
from app.catalogo.schemas import (
    CategoriaActualizar,
    CategoriaCrear,
    ColeccionActualizar,
    ColeccionCrear,
    ColorActualizar,
    ColorCrear,
    MaterialActualizar,
    MaterialCrear,
    ProductoActualizar,
    ProductoCrear,
    TablaMedidaActualizar,
    TablaMedidaCrear,
    TallaActualizar,
    TallaCrear,
    TemporadaActualizar,
    TemporadaCrear,
    VarianteActualizar,
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


class ProductoRepository(CRUDBase[Producto, ProductoCrear, ProductoActualizar]):
    def __init__(self) -> None:
        super().__init__(Producto)

    def obtener_por_codigo(self, db: Session, codigo: str) -> Producto | None:
        return db.scalar(select(Producto).where(Producto.codigo == codigo))

    def crear(self, db: Session, datos: ProductoCrear, creado_por: int | None) -> Producto:
        # ProductoCrear trae tallas_ids/colores_ids para la combinatoria de
        # variantes (los resuelve el service); acá solo se persiste la fila
        # de producto en sí.
        if self.obtener_por_codigo(db, datos.codigo) is not None:
            raise ConflictoError("Ya existe un producto con ese código")
        campos = datos.model_dump(exclude={"tallas_ids", "colores_ids"})
        producto = Producto(**campos, creado_por=creado_por)
        db.add(producto)
        db.commit()
        db.refresh(producto)
        return producto


class VarianteRepository(CRUDBase[ProductoVariante, VarianteActualizar, VarianteActualizar]):
    def __init__(self) -> None:
        super().__init__(ProductoVariante)

    def listar_por_producto(self, db: Session, producto_id: int) -> list[ProductoVariante]:
        return list(
            db.scalars(
                select(ProductoVariante).where(
                    ProductoVariante.producto_id == producto_id, ProductoVariante.activo.is_(True)
                )
            )
        )

    def obtener_por_combinacion(
        self, db: Session, producto_id: int, talla_id: int, color_id: int
    ) -> ProductoVariante | None:
        return db.scalar(
            select(ProductoVariante).where(
                ProductoVariante.producto_id == producto_id,
                ProductoVariante.talla_id == talla_id,
                ProductoVariante.color_id == color_id,
            )
        )

    def obtener_por_sku(self, db: Session, sku: str) -> ProductoVariante | None:
        return db.scalar(select(ProductoVariante).where(ProductoVariante.sku == sku))


class TablaMedidaRepository:
    """No hereda de CRUDBase: tabla_medida no tiene columna `activo`, las
    filas se eliminan físicamente (igual que horario_sucursal)."""

    def listar_por_producto(self, db: Session, producto_id: int) -> list[TablaMedida]:
        return list(db.scalars(select(TablaMedida).where(TablaMedida.producto_id == producto_id)))

    def obtener(self, db: Session, producto_id: int, medida_id: int) -> TablaMedida:
        medida = db.scalar(
            select(TablaMedida).where(TablaMedida.id == medida_id, TablaMedida.producto_id == producto_id)
        )
        if medida is None:
            raise NoEncontradoError("Medida no encontrada")
        return medida

    def crear(self, db: Session, producto_id: int, datos: TablaMedidaCrear) -> TablaMedida:
        medida = TablaMedida(producto_id=producto_id, **datos.model_dump())
        db.add(medida)
        db.commit()
        db.refresh(medida)
        return medida

    def actualizar(
        self, db: Session, producto_id: int, medida_id: int, datos: TablaMedidaActualizar
    ) -> TablaMedida:
        medida = self.obtener(db, producto_id, medida_id)
        for campo, valor in datos.model_dump(exclude_unset=True).items():
            setattr(medida, campo, valor)
        db.commit()
        db.refresh(medida)
        return medida

    def eliminar(self, db: Session, producto_id: int, medida_id: int) -> None:
        medida = self.obtener(db, producto_id, medida_id)
        db.delete(medida)
        db.commit()
