import datetime as dt
from collections import defaultdict

from sqlalchemy.orm import Session

from app.catalogo import service as catalogo_service
from app.catalogo.schemas import CatalogoItemRespuesta, FiltrosCatalogo
from app.core.deps import DIAS_PERIODO_POR_DEFECTO, ParametrosPaginacion, ParametrosPeriodo
from app.inteligencia.groq_cliente import (
    obtener_parser_reporte_voz,
    obtener_parser_voz,
    obtener_rankeador_recomendacion,
)
from app.inteligencia.repository import ConsultaVozRepository, HistorialNavegacionRepository, RecomendacionRepository
from app.inteligencia.schemas import (
    GENEROS_VALIDOS,
    TIPOS_REPORTE_VALIDOS,
    CandidatoRecomendacion,
    EventoCrear,
    PerfilClienteRecomendacion,
    RecomendacionItemRespuesta,
    RecomendacionesRespuesta,
    ReporteVozRespuesta,
    VozRespuesta,
)
from app.inventario import service as inventario_service
from app.organizacion import service as organizacion_service
from app.probador import service as probador_service
from app.reportes import service as reportes_service
from app.seguridad import service as seguridad_service
from app.ventas import service as ventas_service

repo = ConsultaVozRepository()
historial_repo = HistorialNavegacionRepository()
recomendacion_repo = RecomendacionRepository()

CANTIDAD_RESULTADOS = 20

CANTIDAD_CANDIDATOS = 20
CANTIDAD_FINAL = 6

_PESO_TIPO_EVENTO = {"favorito": 3.0, "carrito": 2.5, "vista": 1.0, "busqueda": 0.5}
_PESO_PROBADOR = 2.0

_MOTIVO_GENERICO_HISTORIAL = "Basado en lo que viste recientemente"
_MOTIVO_GENERICO_POPULAR = "Popular esta temporada"


def _genero_valido(genero: str | None) -> str | None:
    """Groq puede devolver cualquier string en `genero`; solo se usa como
    filtro si matchea uno de los cuatro valores que catalogo.schemas.Genero
    acepta (case-insensitive), si no se descarta ese campo sin romper el
    resto de la búsqueda."""
    if genero and genero.strip().lower() in GENEROS_VALIDOS:
        return genero.strip().lower()
    return None


def buscar_por_voz(db: Session, texto: str, usuario) -> VozRespuesta:
    """POST /api/v1/ia/voz. `usuario` es `None` en búsqueda anónima (ver
    get_current_user_opcional)."""
    valores = catalogo_service.listar_valores_referencia(db)
    filtros_voz = obtener_parser_voz().parsear(texto, valores)

    etiquetas: dict[str, str] = {}
    if filtros_voz is None:
        # Groq no configurado, falló, o su JSON no validó: fallback
        # explícito a búsqueda de texto plano sobre el catálogo.
        filtros = FiltrosCatalogo(texto=texto)
    else:
        filtros = catalogo_service.resolver_filtros_por_nombre(
            db,
            categoria=filtros_voz.categoria,
            material=filtros_voz.material,
            color=filtros_voz.color,
            talla=filtros_voz.talla,
            temporada=filtros_voz.temporada,
            genero=_genero_valido(filtros_voz.genero),
            precio_max=filtros_voz.precio_max,
        )
        sucursal_id = organizacion_service.resolver_sucursal_por_nombre(db, filtros_voz.sucursal)
        filtros = filtros.model_copy(update={"sucursal_id": sucursal_id})

        if filtros.categoria_id is not None:
            etiquetas["categoria"] = filtros_voz.categoria
        if filtros.material_id is not None:
            etiquetas["material"] = filtros_voz.material
        if filtros.color_id is not None:
            etiquetas["color"] = filtros_voz.color
        if filtros.talla_id is not None:
            etiquetas["talla"] = filtros_voz.talla
        if filtros.temporada_id is not None:
            etiquetas["temporada"] = filtros_voz.temporada
        if filtros.genero is not None:
            etiquetas["genero"] = filtros.genero
        if filtros.precio_max is not None:
            etiquetas["precio_max"] = str(filtros.precio_max)
        if sucursal_id is not None:
            etiquetas["sucursal"] = filtros_voz.sucursal

    paginacion = ParametrosPaginacion(pagina=1, tamanio=CANTIDAD_RESULTADOS)
    resultados = catalogo_service.buscar_catalogo(db, paginacion, filtros)

    cliente_id = seguridad_service.obtener_perfil_cliente(db, usuario.id).id if usuario else None
    # mode="json": precio_max es Decimal, y el encoder JSON estándar que usa
    # psycopg para la columna JSONB no lo serializa (a diferencia de la
    # respuesta HTTP, que pasa por el jsonable_encoder de FastAPI).
    filtros_json = filtros_voz.model_dump(mode="json") if filtros_voz is not None else {"texto": texto}
    repo.crear(db, cliente_id, texto, filtros_json, len(resultados))

    return VozRespuesta(resultados=resultados, filtros=filtros, etiquetas=etiquetas, cantidad=len(resultados))


def registrar_evento(db: Session, datos: EventoCrear, usuario) -> None:
    """POST /api/v1/ia/eventos. `usuario` es `None` en navegación anónima."""
    cliente_id = seguridad_service.obtener_perfil_cliente(db, usuario.id).id if usuario else None
    historial_repo.crear(db, cliente_id, None, datos.producto_id, datos.variante_id, datos.tipo_evento)


def _candidatos_por_reglas(db: Session, cliente_id: int | None, excluir_producto_id: int | None) -> set[int]:
    """Capa 1: variantes con stock disponible, de temporada vigente,
    excluyendo lo ya comprado por el cliente. Si eso deja cero candidatos
    (temporada sin stock, caso límite) se relaja a "cualquier variante con
    stock" -- nunca se devuelve una lista vacía por esta capa."""
    candidatos = inventario_service.listar_variantes_con_stock(db)
    vigentes = catalogo_service.listar_variantes_temporada_vigente(db)
    if vigentes:
        candidatos &= vigentes
    if cliente_id is not None:
        candidatos -= ventas_service.listar_variantes_compradas(db, cliente_id)
    if excluir_producto_id is not None:
        candidatos -= catalogo_service.listar_variantes_de_producto(db, excluir_producto_id)

    if not candidatos:
        candidatos = inventario_service.listar_variantes_con_stock(db)
        if excluir_producto_id is not None:
            candidatos -= catalogo_service.listar_variantes_de_producto(db, excluir_producto_id)

    return candidatos


def _top_variantes(db: Session, cliente_id: int | None, candidatos: set[int]) -> tuple[list[int], bool]:
    """Capa 2: pondera candidatos según historial_navegacion (peso por tipo
    de evento, más peso a lo reciente) y uso del probador. Sin historial
    (cliente nuevo o anónimo) cae a popularidad por ventas de la temporada
    vigente. Devuelve (top 20 ids, True si vino de historial real)."""
    puntajes: dict[int, float] = defaultdict(float)
    if cliente_id is not None:
        ahora = dt.datetime.now()
        for evento in historial_repo.listar_reciente_por_cliente(db, cliente_id, limite=100):
            if evento.variante_id is None or evento.variante_id not in candidatos:
                continue
            antiguedad_dias = max((ahora - evento.creado_en).days, 0)
            peso = _PESO_TIPO_EVENTO.get(evento.tipo_evento, 0.5)
            puntajes[evento.variante_id] += peso / (1 + antiguedad_dias)

        for sesion in probador_service.listar_sesiones_recientes_cliente(db, cliente_id, limite=50):
            if sesion.variante_id not in candidatos:
                continue
            antiguedad_dias = max((ahora - sesion.creado_en).days, 0)
            puntajes[sesion.variante_id] += _PESO_PROBADOR / (1 + antiguedad_dias)

    if puntajes:
        ordenados = sorted(puntajes, key=puntajes.get, reverse=True)
        resto = [v for v in candidatos if v not in puntajes]
        return (ordenados + resto)[:CANTIDAD_CANDIDATOS], True

    conteo = ventas_service.contar_ventas_por_variante(db, list(candidatos))
    ordenados = sorted(candidatos, key=lambda v: conteo.get(v, 0), reverse=True)
    return ordenados[:CANTIDAD_CANDIDATOS], False


def _colapsar_por_producto(items: dict[int, CatalogoItemRespuesta], orden: list[int]) -> list[int]:
    """De varias variantes candidatas del mismo producto se queda con la
    de mejor puntaje (la primera en `orden`) -- el carrusel muestra
    tarjetas de producto, no de talla/color."""
    vistos: set[int] = set()
    resultado: list[int] = []
    for variante_id in orden:
        item = items.get(variante_id)
        if item is None or item.id in vistos:
            continue
        vistos.add(item.id)
        resultado.append(variante_id)
    return resultado


def obtener_recomendaciones(db: Session, usuario, excluir_producto_id: int | None = None) -> RecomendacionesRespuesta:
    """POST /api/v1/ia/recomendaciones. `usuario` es `None` en navegación
    anónima -- se calcula y devuelve la recomendación igual, pero no se
    persiste (recomendacion.cliente_id es NOT NULL, no hay a quién
    asociarla)."""
    cliente_id = seguridad_service.obtener_perfil_cliente(db, usuario.id).id if usuario else None

    candidatos = _candidatos_por_reglas(db, cliente_id, excluir_producto_id)
    if not candidatos:
        return RecomendacionesRespuesta(recomendaciones=[])

    top_ids, hay_historial = _top_variantes(db, cliente_id, candidatos)
    items = catalogo_service.listar_items_por_variantes(db, top_ids)
    top_ids = _colapsar_por_producto(items, top_ids)

    candidatos_groq = [
        CandidatoRecomendacion(
            variante_id=v,
            nombre=items[v].nombre,
            categoria_id=items[v].categoria_id,
            precio_base=items[v].precio_base,
        )
        for v in top_ids
    ]
    resultado_groq = obtener_rankeador_recomendacion().rankear(
        candidatos_groq, PerfilClienteRecomendacion(hay_historial=hay_historial)
    )

    ids_validos = {c.variante_id for c in candidatos_groq}
    finales: list[tuple[int, str]] = []
    if resultado_groq:
        finales = [(fila.variante_id, fila.motivo) for fila in resultado_groq if fila.variante_id in ids_validos]
        finales = finales[:CANTIDAD_FINAL]

    if not finales:
        motivo_generico = _MOTIVO_GENERICO_HISTORIAL if hay_historial else _MOTIVO_GENERICO_POPULAR
        finales = [(v, motivo_generico) for v in top_ids[:CANTIDAD_FINAL]]

    recomendaciones = [
        RecomendacionItemRespuesta(variante_id=v, producto=items[v], motivo=motivo)
        for v, motivo in finales
        if v in items
    ]

    if cliente_id is not None and recomendaciones:
        recomendacion_repo.crear_lote(
            db, cliente_id, [(r.variante_id, None, r.motivo) for r in recomendaciones]
        )

    return RecomendacionesRespuesta(recomendaciones=recomendaciones)


def generar_reporte_por_voz(db: Session, texto: str) -> ReporteVozRespuesta:
    """POST /api/v1/ia/reporte-voz. Requiere `reportes.ver` (verificado en
    el router, no acá). Groq solo elige `tipo_reporte` (uno de 4 valores
    fijos) y filtros ya conocidos (fechas, nombres) -- nunca genera SQL ni
    texto que se ejecute; si falla o no valida, cae al dashboard con el
    período por defecto, nunca a un error."""
    filtros_voz = obtener_parser_reporte_voz().parsear(texto)

    tipo_reporte = "dashboard"
    if filtros_voz is not None and filtros_voz.tipo_reporte in TIPOS_REPORTE_VALIDOS:
        tipo_reporte = filtros_voz.tipo_reporte

    hasta = filtros_voz.hasta if filtros_voz and filtros_voz.hasta else dt.date.today()
    desde = (
        filtros_voz.desde
        if filtros_voz and filtros_voz.desde
        else hasta - dt.timedelta(days=DIAS_PERIODO_POR_DEFECTO)
    )
    if desde > hasta:
        # Groq mandó un rango invertido: se intercambia en vez de romper.
        desde, hasta = hasta, desde
    periodo = ParametrosPeriodo(desde=desde, hasta=hasta)

    sucursal_id = organizacion_service.resolver_sucursal_por_nombre(db, filtros_voz.sucursal) if filtros_voz else None
    categoria_id = catalogo_service.resolver_categoria_por_nombre(db, filtros_voz.categoria) if filtros_voz else None
    canal = filtros_voz.canal if filtros_voz and filtros_voz.canal in {"digital", "presencial"} else None

    if tipo_reporte == "ventas":
        resultado = reportes_service.reporte_ventas(db, periodo, sucursal_id, categoria_id, canal)
    elif tipo_reporte == "inventario":
        resultado = reportes_service.reporte_inventario(db, sucursal_id)
    elif tipo_reporte == "reservas":
        resultado = reportes_service.reporte_reservas(db, periodo, sucursal_id)
    else:
        resultado = reportes_service.reporte_dashboard(db, periodo, sucursal_id)

    filtros_aplicados = {
        "desde": str(periodo.desde),
        "hasta": str(periodo.hasta),
        "sucursal_id": sucursal_id,
        "categoria_id": categoria_id,
        "canal": canal,
    }
    return ReporteVozRespuesta(
        tipo_reporte=tipo_reporte,
        filtros_aplicados=filtros_aplicados,
        resultado=resultado.model_dump(mode="json"),
    )
