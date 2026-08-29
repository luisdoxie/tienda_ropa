import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictoError, DomainError, NoEncontradoError
from app.catalogo.models import (
    Categoria,
    Coleccion,
    Color,
    Producto,
    ProductoVariante,
    Talla,
    TablaMedida,
    Temporada,
)
from app.catalogo.repository import (
    CategoriaRepository,
    ColeccionRepository,
    ColorRepository,
    MaterialRepository,
    ProductoRepository,
    TablaMedidaRepository,
    TallaRepository,
    TemporadaRepository,
    VarianteRepository,
)
from app.catalogo.schemas import (
    CategoriaActualizar,
    CategoriaCrear,
    ColeccionActualizar,
    ColeccionCrear,
    ProductoActualizar,
    ProductoCrear,
    TablaMedidaActualizar,
    TablaMedidaCrear,
    TemporadaActualizar,
    VarianteActualizar,
    VariantesGenerarRequest,
)

categoria_repo = CategoriaRepository()
temporada_repo = TemporadaRepository()
coleccion_repo = ColeccionRepository()
talla_repo = TallaRepository()
color_repo = ColorRepository()
material_repo = MaterialRepository()
producto_repo = ProductoRepository()
variante_repo = VarianteRepository()
medida_repo = TablaMedidaRepository()

# CLAUDE.md: "Alcance del probador virtual: solo prendas superiores
# masculinas (poleras, camisas, chamarras)". No hay columna en `categoria`
# para marcar esto, así que se resuelve por nombre. Si el admin manda
# admite_probador=True en una categoría que no matchea acá, se ignora.
PALABRAS_TORSO_SUPERIOR = {"polera", "camisa", "chamarra"}


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
    tiene_productos = db.scalar(
        select(Producto).where(Producto.categoria_id == categoria_id, Producto.activo.is_(True))
    )
    if tiene_productos is not None:
        raise ConflictoError("No se puede desactivar: la categoría tiene productos activos")
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


# ---- Producto y variantes ---------------------------------------------------


def _es_torso_superior(db: Session, categoria: Categoria) -> bool:
    actual: Categoria | None = categoria
    visitados: set[int] = set()
    while actual is not None and actual.id not in visitados:
        visitados.add(actual.id)
        nombre = actual.nombre.strip().lower()
        if any(palabra in nombre for palabra in PALABRAS_TORSO_SUPERIOR):
            return True
        actual = db.get(Categoria, actual.categoria_padre_id) if actual.categoria_padre_id else None
    return False


def _resolver_admite_probador(db: Session, categoria_id: int, admite_probador_pedido: bool) -> bool:
    if not admite_probador_pedido:
        return False
    categoria = categoria_repo.obtener(db, categoria_id)
    return _es_torso_superior(db, categoria)


def _validar_referencias_producto(
    db: Session,
    categoria_id: int | None,
    material_id: int | None,
    temporada_id: int | None,
    coleccion_id: int | None,
) -> None:
    if categoria_id is not None:
        categoria_repo.obtener(db, categoria_id)
    if material_id is not None:
        material_repo.obtener(db, material_id)
    if temporada_id is not None:
        temporada_repo.obtener(db, temporada_id)
    if coleccion_id is not None:
        coleccion_repo.obtener(db, coleccion_id)


def crear_producto(db: Session, datos: ProductoCrear, creado_por: int | None) -> Producto:
    _validar_referencias_producto(db, datos.categoria_id, datos.material_id, datos.temporada_id, datos.coleccion_id)

    admite_probador_real = _resolver_admite_probador(db, datos.categoria_id, datos.admite_probador)
    datos = datos.model_copy(update={"admite_probador": admite_probador_real})

    producto = producto_repo.crear(db, datos, creado_por)
    generar_variantes(db, producto, datos.tallas_ids, datos.colores_ids)
    return producto


def actualizar_producto(db: Session, producto_id: int, datos: ProductoActualizar) -> Producto:
    producto = producto_repo.obtener(db, producto_id)
    _validar_referencias_producto(
        db, datos.categoria_id, datos.material_id, datos.temporada_id, datos.coleccion_id
    )

    cambia_categoria = "categoria_id" in datos.model_fields_set
    cambia_probador = "admite_probador" in datos.model_fields_set
    if cambia_categoria or cambia_probador:
        categoria_id = datos.categoria_id if cambia_categoria else producto.categoria_id
        admite_probador_pedido = datos.admite_probador if cambia_probador else producto.admite_probador
        datos = datos.model_copy(
            update={"admite_probador": _resolver_admite_probador(db, categoria_id, admite_probador_pedido)}
        )

    return producto_repo.actualizar(db, producto_id, datos)


def _slug_color(nombre: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", nombre).upper()


def _sku_unico(db: Session, sku_base: str) -> str:
    sku = sku_base
    sufijo = 2
    while variante_repo.obtener_por_sku(db, sku) is not None:
        sku = f"{sku_base}-{sufijo}"
        sufijo += 1
    return sku


def _obtener_tallas(db: Session, tallas_ids: list[int]) -> list[Talla]:
    ids_unicos = set(tallas_ids)
    tallas = list(db.scalars(select(Talla).where(Talla.id.in_(ids_unicos))))
    if len(tallas) != len(ids_unicos):
        raise NoEncontradoError("Una o más tallas no existen")
    return tallas


def _obtener_colores(db: Session, colores_ids: list[int]) -> list[Color]:
    ids_unicos = set(colores_ids)
    colores = list(db.scalars(select(Color).where(Color.id.in_(ids_unicos))))
    if len(colores) != len(ids_unicos):
        raise NoEncontradoError("Uno o más colores no existen")
    return colores


def generar_variantes(
    db: Session, producto: Producto, tallas_ids: list[int], colores_ids: list[int]
) -> list[ProductoVariante]:
    """Combinatoria talla × color con SKU {codigo_producto}-{codigo_talla}-{codigo_color}.

    Si una combinación ya existe (mismo producto_id + talla_id + color_id)
    se salta: llamar esto de nuevo agregando un color no duplica las
    variantes que ya estaban."""
    tallas = _obtener_tallas(db, tallas_ids)
    colores = _obtener_colores(db, colores_ids)

    creadas: list[ProductoVariante] = []
    for talla in tallas:
        for color in colores:
            if variante_repo.obtener_por_combinacion(db, producto.id, talla.id, color.id) is not None:
                continue
            sku_base = f"{producto.codigo}-{talla.codigo}-{_slug_color(color.nombre)}".upper()
            sku = _sku_unico(db, sku_base)
            variante = ProductoVariante(producto_id=producto.id, talla_id=talla.id, color_id=color.id, sku=sku)
            db.add(variante)
            creadas.append(variante)

    db.commit()
    for variante in creadas:
        db.refresh(variante)
    return creadas


def agregar_variantes(db: Session, producto_id: int, datos: VariantesGenerarRequest) -> list[ProductoVariante]:
    producto = producto_repo.obtener(db, producto_id)
    return generar_variantes(db, producto, datos.tallas_ids, datos.colores_ids)


def actualizar_variante(db: Session, variante_id: int, datos: VarianteActualizar) -> ProductoVariante:
    if datos.activo is False:
        # TODO(P3.1): bloquear si stock.cantidad_fisica > 0 una vez que
        # exista el paquete `inventario`. Cuando exista, esto llama a
        # inventario.service, nunca consulta la tabla stock directamente.
        pass
    return variante_repo.actualizar(db, variante_id, datos)


def desactivar_variante(db: Session, variante_id: int) -> ProductoVariante:
    # Mismo TODO que actualizar_variante: bloquear si hay stock físico
    # cuando exista `inventario` (P3.1).
    return variante_repo.desactivar(db, variante_id)


# ---- Tabla de medidas ---------------------------------------------------------


def crear_medida(db: Session, producto_id: int, datos: TablaMedidaCrear) -> TablaMedida:
    producto_repo.obtener(db, producto_id)
    talla_repo.obtener(db, datos.talla_id)
    return medida_repo.crear(db, producto_id, datos)


def actualizar_medida(db: Session, producto_id: int, medida_id: int, datos: TablaMedidaActualizar) -> TablaMedida:
    if datos.talla_id is not None:
        talla_repo.obtener(db, datos.talla_id)
    return medida_repo.actualizar(db, producto_id, medida_id, datos)
