"""Seed de datos de demostración: organización, catálogo y stock inicial.

Cubre la tarea 4 de la ETAPA 7 del plan de desarrollo (carga de datos de
demostración). A diferencia de los otros `seed_*.py`, que solo cargan tablas
de referencia, éste crea datos de negocio: sucursales, catálogos simples,
productos, variantes y existencias.

Dos reglas de CLAUDE.md mandan acá:

- El stock NUNCA se inserta a mano. Se crea llamando a
  `inventario.service.registrar_movimiento()` con el tipo `recepcion`, que es
  lo que bloquea la fila (SELECT FOR UPDATE), valida invariantes y alimenta el
  costo promedio ponderado. Así el kardex queda con historial real.
- Las imágenes van por `catalogo.service.subir_imagen_producto()`, que sube a
  Cloudinary y guarda el public_id (la columna `producto_imagen.url` guarda el
  public_id, no una URL: ver el docstring de `core/storage.py`).

Las imágenes solo se cargan si hay credenciales de Cloudinary configuradas y
si existe el material preparado por `scripts/preparar_dataset.py`. Si falta
cualquiera de las dos cosas el seed corre igual, avisa, y las imágenes se
pueden agregar después volviendo a correrlo.

Idempotente: correrlo más de una vez no duplica ninguna fila.

Uso:
    .venv/Scripts/python -m scripts.seed_demo
"""

from __future__ import annotations

import json
import random
from decimal import Decimal
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.catalogo import service as catalogo_service
from app.catalogo.models import (
    Categoria,
    Coleccion,
    Color,
    Material,
    Producto,
    ProductoImagen,
    ProductoVariante,
    Talla,
    Temporada,
)
from app.inventario import service as inventario_service
from app.inventario.models import Stock
from app.organizacion.models import Ciudad, Sucursal
from app.seguridad.models import Rol, Usuario
from app.core.security import hash_password

DIR_DATOS = Path(__file__).parent / "datos"
ARCHIVO_PRENDAS = DIR_DATOS / "prendas.json"
ARCHIVO_EXTRAS = DIR_DATOS / "extras.json"

ADMIN_EMAIL = "admin@fashionstore.com"
ADMIN_PASSWORD = "Admin123!"

# --- Organización ---------------------------------------------------------

CIUDADES: list[tuple[str, str]] = [
    ("Santa Cruz de la Sierra", "Santa Cruz"),  # ya existe; se reutiliza
    ("Cochabamba", "Cochabamba"),
]

# codigo, nombre, ciudad, direccion, telefono
SUCURSALES: list[tuple[str, str, str, str, str]] = [
    ("SC-EQP", "Casa Matriz Equipetrol", "Santa Cruz de la Sierra",
     "Av. San Martín esq. 3er anillo interno", "33445566"),
    ("SC-VEN", "Sucursal Ventura Mall", "Santa Cruz de la Sierra",
     "Av. San Martín, Ventura Mall, planta baja", "33445577"),
    ("CB-REC", "Sucursal Recoleta", "Cochabamba",
     "Av. Pando esq. Portales, zona Recoleta", "44556677"),
]

# --- Catálogos simples ----------------------------------------------------

# nombre, descripcion, admite_probador
CATEGORIAS: list[tuple[str, str, bool]] = [
    ("Poleras", "Prendas superiores de punto, manga corta o larga", True),
    ("Camisas", "Prendas superiores con botones y cuello", True),
    ("Chamarras", "Abrigos livianos y casacas", True),
    ("Chompas", "Prendas superiores tejidas de abrigo", True),
    ("Buzos", "Prendas deportivas superiores con o sin capucha", True),
    ("Pantalones", "Prendas inferiores largas", False),
    ("Bermudas", "Prendas inferiores cortas", False),
]

COLORES: list[tuple[str, str]] = [
    ("Negro", "#111111"),
    ("Blanco", "#FFFFFF"),
    ("Gris", "#6B7280"),
    ("Gris jaspeado", "#9CA3AF"),
    ("Azul marino", "#1E293B"),
    ("Azul", "#1E3A8A"),
    ("Celeste", "#7DD3FC"),
    ("Verde militar", "#4B5320"),
    ("Beige", "#D6C8B0"),
    ("Café", "#78503C"),
    ("Bordó", "#7F1D1D"),
    ("Mostaza", "#D4A017"),
]

TEMPORADAS: list[tuple[str, int]] = [
    ("Verano", 2026),
    ("Otoño", 2026),
    ("Invierno", 2026),
    ("Primavera", 2026),
]

# nombre, temporada, descripcion
COLECCIONES: list[tuple[str, str, str]] = [
    ("Urbano 2026", "Verano", "Línea casual de uso diario"),
    ("Clásicos", "Otoño", "Prendas atemporales de vestir"),
    ("Abrigo 2026", "Invierno", "Línea de abrigo para temporada fría"),
]

# --- Productos generados --------------------------------------------------
# codigo, nombre, categoria, material, temporada, coleccion, precio_base, colores
PRODUCTOS: list[tuple[str, str, str, str, str, str, str, list[str]]] = [
    ("POL-001", "Polera básica de algodón", "Poleras", "Algodon", "Verano", "Urbano 2026", "89.00", ["Negro", "Blanco", "Gris"]),
    ("POL-002", "Polera cuello V", "Poleras", "Algodon", "Verano", "Urbano 2026", "95.00", ["Blanco", "Azul marino"]),
    ("POL-003", "Polera oversize estampada", "Poleras", "Algodon", "Verano", "Urbano 2026", "120.00", ["Negro", "Beige"]),
    ("POL-004", "Polera manga larga", "Poleras", "Algodon", "Otoño", "Clásicos", "135.00", ["Gris jaspeado", "Bordó"]),
    ("POL-005", "Polera piqué con cuello", "Poleras", "Algodon", "Primavera", "Urbano 2026", "149.00", ["Azul", "Blanco", "Verde militar"]),
    ("CAM-001", "Camisa de lino manga corta", "Camisas", "Lino", "Verano", "Urbano 2026", "210.00", ["Blanco", "Celeste"]),
    ("CAM-002", "Camisa oxford clásica", "Camisas", "Algodon", "Otoño", "Clásicos", "245.00", ["Celeste", "Blanco"]),
    ("CAM-003", "Camisa a cuadros de franela", "Camisas", "Algodon", "Invierno", "Abrigo 2026", "265.00", ["Bordó", "Verde militar"]),
    ("CAM-004", "Camisa denim", "Camisas", "Mezclilla", "Otoño", "Urbano 2026", "280.00", ["Azul", "Azul marino"]),
    ("CAM-005", "Camisa formal slim fit", "Camisas", "Algodon", "Otoño", "Clásicos", "295.00", ["Blanco", "Negro"]),
    ("CHA-001", "Chamarra de cuero sintético", "Chamarras", "Poliester", "Invierno", "Abrigo 2026", "620.00", ["Negro", "Café"]),
    ("CHA-002", "Chamarra bomber", "Chamarras", "Poliester", "Otoño", "Urbano 2026", "480.00", ["Negro", "Verde militar"]),
    ("CHA-003", "Chamarra rompevientos", "Chamarras", "Poliester", "Primavera", "Urbano 2026", "390.00", ["Azul marino", "Gris"]),
    ("CHA-004", "Chamarra de mezclilla", "Chamarras", "Mezclilla", "Otoño", "Urbano 2026", "450.00", ["Azul", "Negro"]),
    ("CHO-001", "Chompa de lana cuello redondo", "Chompas", "Lana", "Invierno", "Abrigo 2026", "340.00", ["Gris", "Bordó", "Azul marino"]),
    ("CHO-002", "Chompa con cierre", "Chompas", "Lana", "Invierno", "Abrigo 2026", "375.00", ["Negro", "Café"]),
    ("CHO-003", "Chaleco tejido", "Chompas", "Lana", "Otoño", "Clásicos", "260.00", ["Beige", "Gris"]),
    ("BUZ-001", "Buzo con capucha", "Buzos", "Algodon", "Invierno", "Abrigo 2026", "310.00", ["Negro", "Gris jaspeado"]),
    ("BUZ-002", "Buzo deportivo cuello redondo", "Buzos", "Algodon", "Otoño", "Urbano 2026", "285.00", ["Azul marino", "Mostaza"]),
    ("PAN-001", "Jean slim fit", "Pantalones", "Mezclilla", "Otoño", "Urbano 2026", "320.00", ["Azul", "Negro"]),
    ("PAN-002", "Pantalón chino", "Pantalones", "Algodon", "Primavera", "Clásicos", "290.00", ["Beige", "Azul marino"]),
    ("PAN-003", "Pantalón cargo", "Pantalones", "Algodon", "Otoño", "Urbano 2026", "335.00", ["Verde militar", "Negro"]),
    ("PAN-004", "Jogger deportivo", "Pantalones", "Algodon", "Invierno", "Urbano 2026", "265.00", ["Gris jaspeado", "Negro"]),
    ("BER-001", "Bermuda de gabardina", "Bermudas", "Algodon", "Verano", "Urbano 2026", "180.00", ["Beige", "Azul marino"]),
    ("BER-002", "Bermuda deportiva", "Bermudas", "Poliester", "Verano", "Urbano 2026", "155.00", ["Negro", "Celeste"]),
]

TALLAS_POR_CATEGORIA = {
    "Poleras": ["S", "M", "L", "XL"],
    "Camisas": ["S", "M", "L", "XL"],
    "Chamarras": ["M", "L", "XL"],
    "Chompas": ["M", "L", "XL"],
    "Buzos": ["S", "M", "L", "XL"],
    "Pantalones": ["S", "M", "L", "XL"],
    "Bermudas": ["S", "M", "L", "XL"],
}

ABREV_COLOR = {
    "Negro": "NEG", "Blanco": "BLA", "Gris": "GRI", "Gris jaspeado": "GRJ",
    "Azul marino": "AZM", "Azul": "AZU", "Celeste": "CEL", "Verde militar": "VER",
    "Beige": "BEI", "Café": "CAF", "Bordó": "BOR", "Mostaza": "MOS",
}


# --- Helpers idempotentes -------------------------------------------------


def _obtener_o_crear(db: Session, modelo, filtros: dict, valores: dict | None = None):
    """Devuelve la fila que cumple `filtros`, creándola si no existe."""
    instancia = db.query(modelo).filter_by(**filtros).one_or_none()
    if instancia is not None:
        return instancia, False
    instancia = modelo(**{**filtros, **(valores or {})})
    db.add(instancia)
    db.flush()
    return instancia, True


def crear_admin(db: Session) -> Usuario:
    usuario = db.query(Usuario).filter(Usuario.email == ADMIN_EMAIL).one_or_none()
    if usuario is not None:
        return usuario

    rol = db.query(Rol).filter(Rol.nombre == "administrador").one_or_none()
    if rol is None:
        raise RuntimeError(
            "No existe el rol 'administrador'. Correr antes: python -m scripts.seed_seguridad"
        )

    usuario = Usuario(
        nombre="Administrador",
        apellido="FashionStore",
        email=ADMIN_EMAIL,
        telefono="70000000",
        password_hash=hash_password(ADMIN_PASSWORD),
    )
    usuario.roles = [rol]
    db.add(usuario)
    db.flush()
    return usuario


def sembrar_organizacion(db: Session) -> dict[str, Sucursal]:
    ciudades: dict[str, Ciudad] = {}
    for nombre, departamento in CIUDADES:
        ciudad, _ = _obtener_o_crear(db, Ciudad, {"nombre": nombre, "departamento": departamento})
        ciudades[nombre] = ciudad

    sucursales: dict[str, Sucursal] = {}
    for codigo, nombre, ciudad_nombre, direccion, telefono in SUCURSALES:
        sucursal, _ = _obtener_o_crear(
            db,
            Sucursal,
            {"codigo": codigo},
            {
                "nombre": nombre,
                "ciudad_id": ciudades[ciudad_nombre].id,
                "direccion": direccion,
                "telefono": telefono,
            },
        )
        sucursales[codigo] = sucursal
    return sucursales


def sembrar_catalogos(db: Session) -> dict:
    categorias: dict[str, Categoria] = {}
    for nombre, descripcion, _probador in CATEGORIAS:
        cat, _ = _obtener_o_crear(db, Categoria, {"nombre": nombre}, {"descripcion": descripcion})
        categorias[nombre] = cat

    colores: dict[str, Color] = {}
    for nombre, hexa in COLORES:
        col, _ = _obtener_o_crear(db, Color, {"nombre": nombre}, {"codigo_hex": hexa})
        colores[nombre] = col

    temporadas: dict[str, Temporada] = {}
    for nombre, anio in TEMPORADAS:
        temp, _ = _obtener_o_crear(db, Temporada, {"nombre": nombre, "anio": anio})
        temporadas[nombre] = temp

    colecciones: dict[str, Coleccion] = {}
    for nombre, temporada_nombre, descripcion in COLECCIONES:
        colec, _ = _obtener_o_crear(
            db,
            Coleccion,
            {"nombre": nombre},
            {"temporada_id": temporadas[temporada_nombre].id, "descripcion": descripcion},
        )
        colecciones[nombre] = colec

    # Tallas y materiales ya los sembró seed_catalogo.py: se reutilizan.
    tallas = {t.codigo: t for t in db.query(Talla).all()}
    materiales = {m.nombre: m for m in db.query(Material).all()}
    if not tallas or not materiales:
        raise RuntimeError(
            "Faltan tallas o materiales. Correr antes: python -m scripts.seed_catalogo"
        )

    return {
        "categorias": categorias,
        "colores": colores,
        "temporadas": temporadas,
        "colecciones": colecciones,
        "tallas": tallas,
        "materiales": materiales,
    }


def _admite_probador(categoria_nombre: str) -> bool:
    return next(flag for nombre, _, flag in CATEGORIAS if nombre == categoria_nombre)


def cargar_prendas_dataset() -> list[tuple]:
    """Prendas del dataset de Kaggle preparadas por `scripts/preparar_dataset.py`.

    El JSON trae las mismas ocho claves que las tuplas de PRODUCTOS más
    `imagen`, de modo que ambas fuentes se siembran por el mismo camino.
    Si el archivo no existe todavía se devuelve una lista vacía: el seed
    corre igual con el catálogo generado.
    """
    if not ARCHIVO_PRENDAS.exists():
        return []

    prendas = json.loads(ARCHIVO_PRENDAS.read_text(encoding="utf-8"))
    return [
        (
            p["codigo"],
            p["nombre"],
            p["categoria"],
            p["material"],
            p["temporada"],
            p["coleccion"],
            p["precio_base"],
            p["colores"],
        )
        for p in prendas
    ]


def sembrar_productos(db: Session, cat: dict, admin: Usuario, productos: list[tuple]) -> list[ProductoVariante]:
    variantes_creadas: list[ProductoVariante] = []

    for codigo, nombre, categoria, material, temporada, coleccion, precio, colores in productos:
        producto, nuevo = _obtener_o_crear(
            db,
            Producto,
            {"codigo": codigo},
            {
                "nombre": nombre,
                "descripcion": f"{nombre}. Prenda de {material.lower()} de la colección {coleccion}.",
                "categoria_id": cat["categorias"][categoria].id,
                "material_id": cat["materiales"][material].id,
                "temporada_id": cat["temporadas"][temporada].id,
                "coleccion_id": cat["colecciones"][coleccion].id,
                "genero": "hombre",
                "precio_base": Decimal(precio),
                "admite_probador": _admite_probador(categoria),
                "creado_por": admin.id,
            },
        )

        for color_nombre in colores:
            color = cat["colores"][color_nombre]
            for talla_codigo in TALLAS_POR_CATEGORIA[categoria]:
                talla = cat["tallas"][talla_codigo]
                sku = f"{codigo}-{talla_codigo}-{ABREV_COLOR[color_nombre]}"
                variante, nueva = _obtener_o_crear(
                    db,
                    ProductoVariante,
                    {"sku": sku},
                    {
                        "producto_id": producto.id,
                        "talla_id": talla.id,
                        "color_id": color.id,
                        "codigo_barras": f"779{abs(hash(sku)) % 10_000_000_000:010d}",
                    },
                )
                if nueva:
                    variantes_creadas.append(variante)

    db.commit()
    return variantes_creadas


def sembrar_stock(db: Session, sucursales: dict[str, Sucursal], admin: Usuario) -> int:
    """Crea existencias mediante movimientos de recepción.

    Nunca escribe en `stock` directamente: `registrar_movimiento` es quien
    bloquea la fila, valida y recalcula el costo promedio ponderado.
    """
    variantes = db.query(ProductoVariante).all()
    lista_sucursales = list(sucursales.values())
    movimientos = 0

    for variante in variantes:
        producto = db.get(Producto, variante.producto_id)
        # Costo aproximado: 55% del precio de lista, con variación por lote.
        costo_base = (producto.precio_base * Decimal("0.55")).quantize(Decimal("0.01"))

        # El azar se deriva del SKU, no de un generador compartido: si una
        # variante ya tiene stock y se saltea, la secuencia no se desincroniza
        # y la próxima corrida elige exactamente las mismas sucursales.
        rng = random.Random(variante.sku)

        # Cada variante entra en 2 o 3 sucursales, no en todas.
        destinos = rng.sample(lista_sucursales, rng.choice([2, 3]))
        for sucursal in destinos:
            ya_tiene = (
                db.query(Stock)
                .filter(Stock.variante_id == variante.id, Stock.sucursal_id == sucursal.id)
                .one_or_none()
            )
            if ya_tiene is not None and ya_tiene.cantidad_fisica > 0:
                continue  # idempotencia: ya se sembró

            cantidad = rng.randint(6, 28)
            variacion = Decimal(rng.choice(["0.92", "0.96", "1.00", "1.05", "1.10"]))
            costo = (costo_base * variacion).quantize(Decimal("0.01"))

            inventario_service.registrar_movimiento(
                db,
                variante_id=variante.id,
                sucursal_id=sucursal.id,
                tipo_movimiento_codigo="recepcion",
                cantidad=cantidad,
                costo_unitario=costo,
                usuario_id=admin.id,
                observacion="Carga inicial de demostración",
                commit=False,
            )
            movimientos += 1

        db.commit()

    # Stock mínimo y máximo: el enunciado los exige y el dashboard los usa
    # para las alertas de reposición.
    for stock in db.query(Stock).all():
        if stock.stock_minimo == 0 and stock.stock_maximo is None:
            rng_stock = random.Random(f"{stock.variante_id}-{stock.sucursal_id}")
            stock.stock_minimo = rng_stock.randint(3, 6)
            stock.stock_maximo = stock.stock_minimo * rng_stock.choice([6, 8, 10])
    db.commit()

    return movimientos


def sembrar_imagenes(db: Session) -> int:
    """Sube a Cloudinary la imagen principal de cada prenda preparada por
    `scripts/preparar_dataset.py`. Si falta Cloudinary o el material, avisa
    y no hace nada: el seed se puede volver a correr después.
    """
    settings = get_settings()
    if not (settings.cloudinary_cloud_name and settings.cloudinary_api_key and settings.cloudinary_api_secret):
        print("  ! Cloudinary sin configurar: se omiten las imágenes.")
        print("    Completar CLOUDINARY_* en backend/.env y volver a correr este seed.")
        return 0

    if not ARCHIVO_PRENDAS.exists():
        print(f"  ! No existe {ARCHIVO_PRENDAS}: se omiten las imágenes.")
        print("    Correr antes: python -m scripts.preparar_dataset")
        return 0

    def _subir(producto: Producto, ruta: Path) -> bool:
        if not ruta.exists():
            print(f"  ! Falta la imagen {ruta.name} de {producto.codigo}")
            return False
        catalogo_service.subir_imagen_producto(
            db,
            producto_id=producto.id,
            contenido=ruta.read_bytes(),
            content_type="image/jpeg",
            color_id=None,
            es_principal=True,
        )
        return True

    def _sin_imagen(producto: Producto) -> bool:
        return db.query(ProductoImagen).filter(ProductoImagen.producto_id == producto.id).count() == 0

    subidas = 0

    # 1. La foto propia de cada prenda traída del dataset.
    for prenda in json.loads(ARCHIVO_PRENDAS.read_text(encoding="utf-8")):
        producto = db.query(Producto).filter(Producto.codigo == prenda["codigo"]).one_or_none()
        if producto is None or not _sin_imagen(producto):
            continue
        if _subir(producto, DIR_DATOS / prenda["imagen"]):
            subidas += 1

    # 2. El excedente, repartido entre los productos del catálogo generado a
    #    mano, que tienen nombre en español pero ninguna imagen propia. Se
    #    asigna por categoría para que la foto corresponda con la prenda.
    if not ARCHIVO_EXTRAS.exists():
        return subidas

    extras: dict[str, list[str]] = json.loads(ARCHIVO_EXTRAS.read_text(encoding="utf-8"))
    for categoria_nombre, rutas in extras.items():
        categoria = db.query(Categoria).filter(Categoria.nombre == categoria_nombre).one_or_none()
        if categoria is None:
            continue
        disponibles = list(rutas)
        productos = (
            db.query(Producto)
            .filter(Producto.categoria_id == categoria.id)
            .order_by(Producto.codigo)
            .all()
        )
        for producto in productos:
            if not disponibles:
                break
            if not _sin_imagen(producto):
                continue
            if _subir(producto, DIR_DATOS / disponibles.pop(0)):
                subidas += 1

    return subidas


def main() -> None:
    db = SessionLocal()
    try:
        print("Sembrando datos de demostración...")

        admin = crear_admin(db)
        db.commit()
        print(f"  - Administrador: {ADMIN_EMAIL}")

        sucursales = sembrar_organizacion(db)
        db.commit()
        print(f"  - Organización: {len(CIUDADES)} ciudades, {len(sucursales)} sucursales")

        cat = sembrar_catalogos(db)
        db.commit()
        print(
            f"  - Catálogos: {len(cat['categorias'])} categorías, {len(cat['colores'])} colores, "
            f"{len(cat['temporadas'])} temporadas, {len(cat['colecciones'])} colecciones"
        )

        del_dataset = cargar_prendas_dataset()
        nuevas = sembrar_productos(db, cat, admin, PRODUCTOS + del_dataset)
        total_prod = db.query(Producto).count()
        total_var = db.query(ProductoVariante).count()
        origen = f"{len(PRODUCTOS)} generados"
        origen += f" + {len(del_dataset)} del dataset" if del_dataset else " (dataset aún no preparado)"
        print(f"  - Catálogo: {total_prod} productos ({origen}), {total_var} variantes ({len(nuevas)} nuevas)")

        movimientos = sembrar_stock(db, sucursales, admin)
        total_stock = db.query(Stock).count()
        print(f"  - Inventario: {total_stock} filas de stock, {movimientos} recepciones nuevas")

        subidas = sembrar_imagenes(db)
        db.commit()
        if subidas:
            print(f"  - Imágenes: {subidas} subidas a Cloudinary")

        print("Seed de demostración aplicado.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
