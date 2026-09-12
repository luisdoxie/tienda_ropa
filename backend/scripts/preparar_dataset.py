"""Prepara una muestra del dataset de Kaggle para el catálogo de demostración.

Dataset: `paramaggarwal/fashion-product-images-dataset` (44.000 prendas con
ficha en CSV). **No se descarga entero** — pesa unos 25 GB. La API de Kaggle
permite bajar archivos sueltos, así que acá se trae solo `styles.csv` y después
las imágenes de las prendas seleccionadas, unos pocos MB en total.

Se corre UNA sola vez. No toca la base de datos: deja el material en
`scripts/datos/` para que `scripts/seed_demo.py` lo consuma.

Genera dos salidas:

- `prendas.json`  — prendas superiores masculinas que se cargan como productos
  nuevos, con su clasificación y su imagen. Son las que admiten probador.
- `extras.json`   — un excedente de imágenes agrupado por categoría, para que
  `seed_demo` les ponga foto a los productos del catálogo generado a mano
  (que tienen nombres en español pero ninguna imagen propia).

Requisito: token de Kaggle. El formato nuevo es un `access_token` en
`%USERPROFILE%\\.kaggle\\access_token` (Kaggle → Settings → API → Create New
API Token); el cliente también acepta el `kaggle.json` clásico.

Uso:
    .venv/Scripts/python -m scripts.preparar_dataset


TAXONOMÍA — cómo se mapea el dataset al esquema de FashionStore
---------------------------------------------------------------
Ésta es la decisión de diseño de la carga: el dataset trae su propia
clasificación y hay que traducirla a las tablas del proyecto.

    gender              -> producto.genero          (Men -> "hombre")
    articleType         -> categoria.nombre         (Tshirts -> "Poleras", ...)
    baseColour          -> color.nombre             (+ hex, ver COLORES en seed_demo)
    season              -> temporada.nombre         (Summer -> "Verano", ...)
    usage               -> se incorpora a producto.descripcion
    productDisplayName  -> producto.nombre
    masterCategory      -> solo filtro (Apparel), no se carga
    subCategory         -> Topwear admite probador; Bottomwear no
    id                  -> nombre del archivo de imagen (images/<id>.jpg)

Lo que el dataset no trae y se asigna acá:
    producto.precio_base    -> rango por categoría (PRECIOS_POR_CATEGORIA)
    producto.material_id    -> material típico por categoría
    producto.coleccion_id   -> colección derivada de la temporada
    producto.admite_probador-> verdadero solo para las prendas superiores

ALCANCE DEL PROBADOR: solo prendas superiores masculinas, según CLAUDE.md.
Ojo: estas imágenes son JPG sobre fondo blanco y sirven para el catálogo,
NO como overlay del probador — ése necesita PNG con canal alfa y hay que
recortarlo aparte.
"""

from __future__ import annotations

import csv
import json
import subprocess
import time
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

DATASET = "paramaggarwal/fashion-product-images-dataset"
# El listado de Kaggle muestra las rutas doblemente anidadas
# (fashion-dataset/fashion-dataset/...) pero la descarga espera una sola.
RAIZ = "fashion-dataset"

DIR_DATOS = Path(__file__).parent / "datos"
DIR_IMAGENES = DIR_DATOS / "imagenes"
ARCHIVO_PRENDAS = DIR_DATOS / "prendas.json"
ARCHIVO_EXTRAS = DIR_DATOS / "extras.json"
ARCHIVO_STYLES = DIR_DATOS / "styles.csv"

# Prendas superiores que se cargan como productos nuevos (las del probador).
CANTIDAD_PRENDAS = 25

# articleType -> categoría de FashionStore. Las superiores admiten probador.
CATEGORIAS_SUPERIORES = {
    "Tshirts": "Poleras",
    "Shirts": "Camisas",
    "Jackets": "Chamarras",
    "Sweaters": "Chompas",
    "Sweatshirts": "Buzos",
}
CATEGORIAS_INFERIORES = {
    "Jeans": "Pantalones",
    "Trousers": "Pantalones",
    "Track Pants": "Pantalones",
    "Shorts": "Bermudas",
}
CATEGORIAS = {**CATEGORIAS_SUPERIORES, **CATEGORIAS_INFERIORES}

# Cuántas imágenes de repuesto hacen falta por categoría: exactamente tantas
# como productos sin foto tiene el catálogo generado en seed_demo.py.
EXTRAS_POR_CATEGORIA = {
    "Poleras": 5,
    "Camisas": 5,
    "Chamarras": 4,
    "Chompas": 3,
    "Buzos": 2,
    "Pantalones": 4,
    "Bermudas": 2,
}

TEMPORADAS = {"Summer": "Verano", "Fall": "Otoño", "Winter": "Invierno", "Spring": "Primavera"}

COLECCIONES = {
    "Verano": "Urbano 2026",
    "Primavera": "Urbano 2026",
    "Otoño": "Clásicos",
    "Invierno": "Abrigo 2026",
}

# baseColour del dataset -> color de FashionStore (los definidos en seed_demo)
COLORES = {
    "Black": "Negro", "White": "Blanco", "Grey": "Gris", "Grey Melange": "Gris jaspeado",
    "Navy Blue": "Azul marino", "Blue": "Azul", "Light Blue": "Celeste",
    "Olive": "Verde militar", "Green": "Verde militar", "Beige": "Beige",
    "Brown": "Café", "Maroon": "Bordó", "Burgundy": "Bordó",
    "Mustard": "Mostaza", "Yellow": "Mostaza",
}

# categoría -> (material típico, precio base en Bs)
PRECIOS_POR_CATEGORIA = {
    "Poleras": ("Algodon", "110.00"),
    "Camisas": ("Algodon", "250.00"),
    "Chamarras": ("Poliester", "470.00"),
    "Chompas": ("Lana", "330.00"),
    "Buzos": ("Algodon", "290.00"),
    "Pantalones": ("Mezclilla", "310.00"),
    "Bermudas": ("Algodon", "170.00"),
}

PREFIJOS = {
    "Poleras": "DPO", "Camisas": "DCA", "Chamarras": "DCH",
    "Chompas": "DCO", "Buzos": "DBU", "Pantalones": "DPA", "Bermudas": "DBE",
}

# El dataset tiene algunas fichas que no corresponden con su imagen: el CSV
# declara una prenda y el archivo muestra otra. Se detectan revisando las
# imágenes descargadas contra su `articleType`, y se anotan acá para que no
# vuelvan a salir elegidas. Verificados a mano el 12/09/2026:
#   1165 - declarado "Men / Tshirts", la imagen es un saco de mujer
#   3323 - declarado "Men / Jackets", la imagen es una polera polo
IDS_DESCARTADOS = {"1165", "3323"}


def _kaggle(*args: str, intentos: int = 4) -> None:
    """Llama al cliente de Kaggle reintentando los cortes de red.

    Bajar decenas de archivos sueltos hace decenas de conexiones, y alguna se
    cae (`ConnectionResetError`). Sin reintento, un corte tira abajo toda la
    preparación a mitad de camino.
    """
    ultimo = ""
    for intento in range(1, intentos + 1):
        proceso = subprocess.run([sys.executable, "-m", "kaggle", *args], capture_output=True, text=True)
        if proceso.returncode == 0:
            return
        ultimo = (proceso.stderr or proceso.stdout).strip()
        if intento < intentos:
            print(f"      reintento {intento}/{intentos - 1} tras fallo de red...")
            time.sleep(2 * intento)
    raise RuntimeError(f"Falló `kaggle {' '.join(args)}`:\n{ultimo}")


def _descomprimir(directorio: Path, patron: str) -> None:
    for candidato in directorio.glob(patron):
        if candidato.suffix == ".zip":
            with zipfile.ZipFile(candidato) as z:
                z.extractall(directorio)
            candidato.unlink()


def descargar_styles() -> Path:
    if ARCHIVO_STYLES.exists():
        print(f"  - styles.csv ya estaba en {ARCHIVO_STYLES.name}")
        return ARCHIVO_STYLES

    print("  - Descargando styles.csv (solo ese archivo, no el dataset entero)...")
    _kaggle("datasets", "download", "-d", DATASET, "-f", f"{RAIZ}/styles.csv",
            "-p", str(DIR_DATOS), "--force")
    _descomprimir(DIR_DATOS, "styles.csv*")
    if not ARCHIVO_STYLES.exists():
        raise RuntimeError(f"No apareció styles.csv en {DIR_DATOS}")
    return ARCHIVO_STYLES


def leer_candidatas(styles: Path) -> list[dict]:
    """Prendas masculinas con categoría, color y temporada que sepamos mapear.

    El CSV trae filas con más comas de las que declara la cabecera (el nombre
    del producto puede llevar comas sin comillas), así que se lee con
    `csv.reader` y se reunifica la última columna en vez de usar DictReader.
    """
    candidatas: list[dict] = []
    with styles.open(encoding="utf-8", errors="ignore", newline="") as f:
        lector = csv.reader(f)
        cabecera = next(lector)
        idx = {nombre: i for i, nombre in enumerate(cabecera)}
        n = len(cabecera)

        for fila in lector:
            if len(fila) < n:
                continue
            if len(fila) > n:
                fila = fila[: n - 1] + [",".join(fila[n - 1:])]

            registro = {k: fila[i] for k, i in idx.items()}
            if registro.get("id") in IDS_DESCARTADOS:
                continue
            if registro.get("gender") != "Men":
                continue
            if registro.get("articleType") not in CATEGORIAS:
                continue
            if registro.get("baseColour") not in COLORES:
                continue
            if registro.get("season") not in TEMPORADAS:
                continue
            registro["_categoria"] = CATEGORIAS[registro["articleType"]]
            registro["_superior"] = registro["articleType"] in CATEGORIAS_SUPERIORES
            candidatas.append(registro)

    return candidatas


def _variadas(grupo: list[dict], cupo: int, usados: set[str]) -> list[dict]:
    """Elige `cupo` prendas del grupo evitando repetir color+temporada."""
    elegidas: list[dict] = []
    vistos: set[tuple[str, str]] = set()
    for registro in sorted(grupo, key=lambda r: int(r["id"])):
        if registro["id"] in usados:
            continue
        clave = (registro["baseColour"], registro["season"])
        if clave in vistos:
            continue
        vistos.add(clave)
        elegidas.append(registro)
        if len(elegidas) >= cupo:
            break
    return elegidas


def seleccionar_prendas(candidatas: list[dict]) -> list[dict]:
    """Prendas superiores que se cargan como productos nuevos."""
    por_categoria: dict[str, list[dict]] = defaultdict(list)
    for c in candidatas:
        if c["_superior"]:
            por_categoria[c["_categoria"]].append(c)

    cupo = max(1, CANTIDAD_PRENDAS // len(por_categoria))
    elegidas: list[dict] = []
    for _categoria, grupo in sorted(por_categoria.items()):
        elegidas.extend(_variadas(grupo, cupo, set()))
    return elegidas[:CANTIDAD_PRENDAS]


def seleccionar_extras(candidatas: list[dict], ya_usados: set[str]) -> dict[str, list[dict]]:
    """Excedente de imágenes por categoría para el catálogo generado a mano."""
    por_categoria: dict[str, list[dict]] = defaultdict(list)
    for c in candidatas:
        por_categoria[c["_categoria"]].append(c)

    extras: dict[str, list[dict]] = {}
    for categoria, cupo in EXTRAS_POR_CATEGORIA.items():
        elegidas = _variadas(por_categoria.get(categoria, []), cupo, ya_usados)
        if len(elegidas) < cupo:
            print(f"    ! Solo {len(elegidas)}/{cupo} imágenes disponibles para {categoria}")
        extras[categoria] = elegidas
    return extras


def descargar_imagenes(registros: list[dict]) -> None:
    DIR_IMAGENES.mkdir(parents=True, exist_ok=True)
    pendientes = [r for r in registros if not (DIR_IMAGENES / f"{r['id']}.jpg").exists()]
    if not pendientes:
        print(f"    ({len(registros)} imágenes ya estaban descargadas)")
        return

    for i, registro in enumerate(pendientes, 1):
        print(f"    [{i}/{len(pendientes)}] {registro['id']}.jpg  {registro['_categoria']}")
        _kaggle("datasets", "download", "-d", DATASET,
                "-f", f"{RAIZ}/images/{registro['id']}.jpg",
                "-p", str(DIR_IMAGENES), "--force")
        _descomprimir(DIR_IMAGENES, f"{registro['id']}.jpg*")


def construir_prendas(seleccionadas: list[dict]) -> list[dict]:
    prendas: list[dict] = []
    contadores: dict[str, int] = defaultdict(int)

    for registro in seleccionadas:
        categoria = registro["_categoria"]
        temporada = TEMPORADAS[registro["season"]]
        material, precio = PRECIOS_POR_CATEGORIA[categoria]

        contadores[categoria] += 1
        prendas.append(
            {
                "codigo": f"{PREFIJOS[categoria]}-{contadores[categoria]:03d}",
                "nombre": registro["productDisplayName"][:120],
                "categoria": categoria,
                "material": material,
                "temporada": temporada,
                "coleccion": COLECCIONES[temporada],
                "precio_base": precio,
                "colores": [COLORES[registro["baseColour"]]],
                "uso": registro.get("usage") or "Casual",
                "imagen": f"imagenes/{registro['id']}.jpg",
                "origen_dataset_id": registro["id"],
            }
        )
    return prendas


def main() -> None:
    DIR_DATOS.mkdir(parents=True, exist_ok=True)

    try:
        import kaggle  # noqa: F401
    except Exception:
        sys.exit(
            "Falta el paquete `kaggle`. Instalarlo con:\n"
            "    .venv/Scripts/python -m pip install kaggle\n"
            "y dejar el token en %USERPROFILE%\\.kaggle\\access_token"
        )

    print("Preparando muestra del dataset...")
    styles = descargar_styles()

    candidatas = leer_candidatas(styles)
    print(f"  - {len(candidatas)} prendas masculinas cumplen el filtro")

    prendas_sel = seleccionar_prendas(candidatas)
    usados = {r["id"] for r in prendas_sel}
    extras_sel = seleccionar_extras(candidatas, usados)
    total_extras = sum(len(v) for v in extras_sel.values())
    print(f"  - Seleccionadas {len(prendas_sel)} prendas nuevas + {total_extras} imágenes de repuesto")

    print("  - Descargando solo esas imágenes...")
    todas = prendas_sel + [r for grupo in extras_sel.values() for r in grupo]
    descargar_imagenes(todas)

    ARCHIVO_PRENDAS.write_text(
        json.dumps(construir_prendas(prendas_sel), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    ARCHIVO_EXTRAS.write_text(
        json.dumps(
            {cat: [f"imagenes/{r['id']}.jpg" for r in grupo] for cat, grupo in extras_sel.items()},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"\nListo: {len(prendas_sel)} prendas en prendas.json y {total_extras} imágenes en extras.json")
    print("Ahora correr:  .venv/Scripts/python -m scripts.seed_demo")


if __name__ == "__main__":
    main()
