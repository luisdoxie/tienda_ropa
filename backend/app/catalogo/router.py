from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import ParametrosPaginacion, parametros_paginacion
from app.core.security import get_current_user, require_permission
from app.catalogo import service
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
    CategoriaRespuesta,
    ColeccionActualizar,
    ColeccionCrear,
    ColeccionRespuesta,
    ColorActualizar,
    ColorCrear,
    ColorRespuesta,
    MaterialActualizar,
    MaterialCrear,
    MaterialRespuesta,
    ProductoActualizar,
    ProductoCrear,
    ProductoRespuesta,
    TablaMedidaActualizar,
    TablaMedidaCrear,
    TablaMedidaRespuesta,
    TallaActualizar,
    TallaCrear,
    TallaRespuesta,
    TemporadaActualizar,
    TemporadaCrear,
    TemporadaRespuesta,
    VarianteActualizar,
    VarianteRespuesta,
    VariantesGenerarRequest,
)

categoria_repo = CategoriaRepository()
talla_repo = TallaRepository()
color_repo = ColorRepository()
material_repo = MaterialRepository()
temporada_repo = TemporadaRepository()
coleccion_repo = ColeccionRepository()
producto_repo = ProductoRepository()
variante_repo = VarianteRepository()
medida_repo = TablaMedidaRepository()

PERMISO_CATALOGO = "catalogo.gestionar"
admin_requerido = Depends(require_permission(PERMISO_CATALOGO))

# ---- /api/v1/categorias ---------------------------------------------------

categorias_router = APIRouter(prefix="/api/v1/categorias", tags=["categorias"])


@categorias_router.get("", response_model=list[CategoriaRespuesta])
def listar_categorias(
    db: Session = Depends(get_db), paginacion: ParametrosPaginacion = Depends(parametros_paginacion)
) -> list[CategoriaRespuesta]:
    return list(categoria_repo.listar(db, paginacion))


@categorias_router.get("/{categoria_id}", response_model=CategoriaRespuesta)
def obtener_categoria(categoria_id: int, db: Session = Depends(get_db)) -> CategoriaRespuesta:
    return categoria_repo.obtener(db, categoria_id)


@categorias_router.post(
    "", response_model=CategoriaRespuesta, status_code=status.HTTP_201_CREATED, dependencies=[admin_requerido]
)
def crear_categoria(datos: CategoriaCrear, db: Session = Depends(get_db)) -> CategoriaRespuesta:
    return service.crear_categoria(db, datos)


@categorias_router.put(
    "/{categoria_id}", response_model=CategoriaRespuesta, dependencies=[admin_requerido]
)
def actualizar_categoria(
    categoria_id: int, datos: CategoriaActualizar, db: Session = Depends(get_db)
) -> CategoriaRespuesta:
    return service.actualizar_categoria(db, categoria_id, datos)


@categorias_router.delete(
    "/{categoria_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[admin_requerido]
)
def desactivar_categoria(categoria_id: int, db: Session = Depends(get_db)) -> None:
    service.desactivar_categoria(db, categoria_id)


# ---- /api/v1/tallas -----------------------------------------------------

tallas_router = APIRouter(prefix="/api/v1/tallas", tags=["tallas"])


@tallas_router.get("", response_model=list[TallaRespuesta])
def listar_tallas(
    db: Session = Depends(get_db), paginacion: ParametrosPaginacion = Depends(parametros_paginacion)
) -> list[TallaRespuesta]:
    return list(talla_repo.listar(db, paginacion))


@tallas_router.get("/{talla_id}", response_model=TallaRespuesta)
def obtener_talla(talla_id: int, db: Session = Depends(get_db)) -> TallaRespuesta:
    return talla_repo.obtener(db, talla_id)


@tallas_router.post(
    "", response_model=TallaRespuesta, status_code=status.HTTP_201_CREATED, dependencies=[admin_requerido]
)
def crear_talla(datos: TallaCrear, db: Session = Depends(get_db)) -> TallaRespuesta:
    return talla_repo.crear(db, datos)


@tallas_router.put("/{talla_id}", response_model=TallaRespuesta, dependencies=[admin_requerido])
def actualizar_talla(talla_id: int, datos: TallaActualizar, db: Session = Depends(get_db)) -> TallaRespuesta:
    return talla_repo.actualizar(db, talla_id, datos)


@tallas_router.delete("/{talla_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[admin_requerido])
def eliminar_talla(talla_id: int, db: Session = Depends(get_db)) -> None:
    talla_repo.eliminar(db, talla_id)


# ---- /api/v1/colores -------------------------------------------------------

colores_router = APIRouter(prefix="/api/v1/colores", tags=["colores"])


@colores_router.get("", response_model=list[ColorRespuesta])
def listar_colores(
    db: Session = Depends(get_db), paginacion: ParametrosPaginacion = Depends(parametros_paginacion)
) -> list[ColorRespuesta]:
    return list(color_repo.listar(db, paginacion))


@colores_router.get("/{color_id}", response_model=ColorRespuesta)
def obtener_color(color_id: int, db: Session = Depends(get_db)) -> ColorRespuesta:
    return color_repo.obtener(db, color_id)


@colores_router.post(
    "", response_model=ColorRespuesta, status_code=status.HTTP_201_CREATED, dependencies=[admin_requerido]
)
def crear_color(datos: ColorCrear, db: Session = Depends(get_db)) -> ColorRespuesta:
    return color_repo.crear(db, datos)


@colores_router.put("/{color_id}", response_model=ColorRespuesta, dependencies=[admin_requerido])
def actualizar_color(color_id: int, datos: ColorActualizar, db: Session = Depends(get_db)) -> ColorRespuesta:
    return color_repo.actualizar(db, color_id, datos)


@colores_router.delete("/{color_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[admin_requerido])
def eliminar_color(color_id: int, db: Session = Depends(get_db)) -> None:
    color_repo.eliminar(db, color_id)


# ---- /api/v1/materiales ---------------------------------------------------

materiales_router = APIRouter(prefix="/api/v1/materiales", tags=["materiales"])


@materiales_router.get("", response_model=list[MaterialRespuesta])
def listar_materiales(
    db: Session = Depends(get_db), paginacion: ParametrosPaginacion = Depends(parametros_paginacion)
) -> list[MaterialRespuesta]:
    return list(material_repo.listar(db, paginacion))


@materiales_router.get("/{material_id}", response_model=MaterialRespuesta)
def obtener_material(material_id: int, db: Session = Depends(get_db)) -> MaterialRespuesta:
    return material_repo.obtener(db, material_id)


@materiales_router.post(
    "", response_model=MaterialRespuesta, status_code=status.HTTP_201_CREATED, dependencies=[admin_requerido]
)
def crear_material(datos: MaterialCrear, db: Session = Depends(get_db)) -> MaterialRespuesta:
    return material_repo.crear(db, datos)


@materiales_router.put(
    "/{material_id}", response_model=MaterialRespuesta, dependencies=[admin_requerido]
)
def actualizar_material(
    material_id: int, datos: MaterialActualizar, db: Session = Depends(get_db)
) -> MaterialRespuesta:
    return material_repo.actualizar(db, material_id, datos)


@materiales_router.delete(
    "/{material_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[admin_requerido]
)
def eliminar_material(material_id: int, db: Session = Depends(get_db)) -> None:
    material_repo.eliminar(db, material_id)


# ---- /api/v1/temporadas ---------------------------------------------------

temporadas_router = APIRouter(prefix="/api/v1/temporadas", tags=["temporadas"])


@temporadas_router.get("", response_model=list[TemporadaRespuesta])
def listar_temporadas(
    db: Session = Depends(get_db), paginacion: ParametrosPaginacion = Depends(parametros_paginacion)
) -> list[TemporadaRespuesta]:
    return list(temporada_repo.listar(db, paginacion))


@temporadas_router.get("/{temporada_id}", response_model=TemporadaRespuesta)
def obtener_temporada(temporada_id: int, db: Session = Depends(get_db)) -> TemporadaRespuesta:
    return temporada_repo.obtener(db, temporada_id)


@temporadas_router.post(
    "", response_model=TemporadaRespuesta, status_code=status.HTTP_201_CREATED, dependencies=[admin_requerido]
)
def crear_temporada(datos: TemporadaCrear, db: Session = Depends(get_db)) -> TemporadaRespuesta:
    return temporada_repo.crear(db, datos)


@temporadas_router.put(
    "/{temporada_id}", response_model=TemporadaRespuesta, dependencies=[admin_requerido]
)
def actualizar_temporada(
    temporada_id: int, datos: TemporadaActualizar, db: Session = Depends(get_db)
) -> TemporadaRespuesta:
    return service.actualizar_temporada(db, temporada_id, datos)


@temporadas_router.delete(
    "/{temporada_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[admin_requerido]
)
def desactivar_temporada(temporada_id: int, db: Session = Depends(get_db)) -> None:
    temporada_repo.desactivar(db, temporada_id)


# ---- /api/v1/colecciones ---------------------------------------------------

colecciones_router = APIRouter(prefix="/api/v1/colecciones", tags=["colecciones"])


@colecciones_router.get("", response_model=list[ColeccionRespuesta])
def listar_colecciones(
    db: Session = Depends(get_db), paginacion: ParametrosPaginacion = Depends(parametros_paginacion)
) -> list[ColeccionRespuesta]:
    return list(coleccion_repo.listar(db, paginacion))


@colecciones_router.get("/{coleccion_id}", response_model=ColeccionRespuesta)
def obtener_coleccion(coleccion_id: int, db: Session = Depends(get_db)) -> ColeccionRespuesta:
    return coleccion_repo.obtener(db, coleccion_id)


@colecciones_router.post(
    "", response_model=ColeccionRespuesta, status_code=status.HTTP_201_CREATED, dependencies=[admin_requerido]
)
def crear_coleccion(datos: ColeccionCrear, db: Session = Depends(get_db)) -> ColeccionRespuesta:
    return service.crear_coleccion(db, datos)


@colecciones_router.put(
    "/{coleccion_id}", response_model=ColeccionRespuesta, dependencies=[admin_requerido]
)
def actualizar_coleccion(
    coleccion_id: int, datos: ColeccionActualizar, db: Session = Depends(get_db)
) -> ColeccionRespuesta:
    return service.actualizar_coleccion(db, coleccion_id, datos)


@colecciones_router.delete(
    "/{coleccion_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[admin_requerido]
)
def desactivar_coleccion(coleccion_id: int, db: Session = Depends(get_db)) -> None:
    coleccion_repo.desactivar(db, coleccion_id)


# ---- /api/v1/productos -----------------------------------------------------
# Estos son de administración (alta/edición de catálogo). El catálogo que
# ve el cliente es otro conjunto de endpoints públicos, GET /api/v1/catalogo/*
# (P2.4) — acá todo requiere permiso de administrador, GET incluido.

productos_router = APIRouter(prefix="/api/v1/productos", tags=["productos"], dependencies=[admin_requerido])


@productos_router.get("", response_model=list[ProductoRespuesta])
def listar_productos(
    db: Session = Depends(get_db), paginacion: ParametrosPaginacion = Depends(parametros_paginacion)
) -> list[ProductoRespuesta]:
    return list(producto_repo.listar(db, paginacion))


@productos_router.get("/{producto_id}", response_model=ProductoRespuesta)
def obtener_producto(producto_id: int, db: Session = Depends(get_db)) -> ProductoRespuesta:
    return producto_repo.obtener(db, producto_id)


@productos_router.post("", response_model=ProductoRespuesta, status_code=status.HTTP_201_CREATED)
def crear_producto(
    datos: ProductoCrear, usuario=Depends(get_current_user), db: Session = Depends(get_db)
) -> ProductoRespuesta:
    return service.crear_producto(db, datos, creado_por=usuario.id)


@productos_router.put("/{producto_id}", response_model=ProductoRespuesta)
def actualizar_producto(
    producto_id: int, datos: ProductoActualizar, db: Session = Depends(get_db)
) -> ProductoRespuesta:
    return service.actualizar_producto(db, producto_id, datos)


@productos_router.delete("/{producto_id}", status_code=status.HTTP_204_NO_CONTENT)
def desactivar_producto(producto_id: int, db: Session = Depends(get_db)) -> None:
    producto_repo.desactivar(db, producto_id)


# ---- /api/v1/productos/{id}/variantes y /api/v1/variantes/{id} -------------


@productos_router.get("/{producto_id}/variantes", response_model=list[VarianteRespuesta])
def listar_variantes(producto_id: int, db: Session = Depends(get_db)) -> list[VarianteRespuesta]:
    producto_repo.obtener(db, producto_id)
    variantes = variante_repo.listar_por_producto(db, producto_id)
    return [VarianteRespuesta.from_modelo(v) for v in variantes]


@productos_router.post(
    "/{producto_id}/variantes", response_model=list[VarianteRespuesta], status_code=status.HTTP_201_CREATED
)
def agregar_variantes(
    producto_id: int, datos: VariantesGenerarRequest, db: Session = Depends(get_db)
) -> list[VarianteRespuesta]:
    variantes = service.agregar_variantes(db, producto_id, datos)
    return [VarianteRespuesta.from_modelo(v) for v in variantes]


variantes_router = APIRouter(prefix="/api/v1/variantes", tags=["variantes"], dependencies=[admin_requerido])


@variantes_router.put("/{variante_id}", response_model=VarianteRespuesta)
def actualizar_variante(
    variante_id: int, datos: VarianteActualizar, db: Session = Depends(get_db)
) -> VarianteRespuesta:
    variante = service.actualizar_variante(db, variante_id, datos)
    return VarianteRespuesta.from_modelo(variante)


@variantes_router.delete("/{variante_id}", status_code=status.HTTP_204_NO_CONTENT)
def desactivar_variante(variante_id: int, db: Session = Depends(get_db)) -> None:
    service.desactivar_variante(db, variante_id)


# ---- /api/v1/productos/{id}/medidas -----------------------------------------


@productos_router.get("/{producto_id}/medidas", response_model=list[TablaMedidaRespuesta])
def listar_medidas(producto_id: int, db: Session = Depends(get_db)) -> list[TablaMedidaRespuesta]:
    producto_repo.obtener(db, producto_id)
    return list(medida_repo.listar_por_producto(db, producto_id))


@productos_router.post(
    "/{producto_id}/medidas", response_model=TablaMedidaRespuesta, status_code=status.HTTP_201_CREATED
)
def crear_medida(
    producto_id: int, datos: TablaMedidaCrear, db: Session = Depends(get_db)
) -> TablaMedidaRespuesta:
    return service.crear_medida(db, producto_id, datos)


@productos_router.put("/{producto_id}/medidas/{medida_id}", response_model=TablaMedidaRespuesta)
def actualizar_medida(
    producto_id: int, medida_id: int, datos: TablaMedidaActualizar, db: Session = Depends(get_db)
) -> TablaMedidaRespuesta:
    return service.actualizar_medida(db, producto_id, medida_id, datos)


@productos_router.delete("/{producto_id}/medidas/{medida_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_medida(producto_id: int, medida_id: int, db: Session = Depends(get_db)) -> None:
    medida_repo.eliminar(db, producto_id, medida_id)


routers = [
    categorias_router,
    tallas_router,
    colores_router,
    materiales_router,
    temporadas_router,
    colecciones_router,
    productos_router,
    variantes_router,
]
