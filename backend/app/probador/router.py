from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_permission
from app.probador import service
from app.probador.schemas import (
    ActivoRespuesta,
    AnclajesActualizar,
    AssetsVarianteRespuesta,
    GeneracionEstadoRespuesta,
    GeneracionIniciadaRespuesta,
    SesionCrear,
    SesionRespuesta,
    TallaRecomendadaRespuesta,
    TallaRequest,
    TipoActivo,
)

PERMISO_PROBADOR = "probador.gestionar"
admin_requerido = Depends(require_permission(PERMISO_PROBADOR))

router = APIRouter(prefix="/api/v1/probador/assets", tags=["probador"], dependencies=[admin_requerido])

uso_router = APIRouter(prefix="/api/v1/probador", tags=["probador"])


@router.get("", response_model=list[ActivoRespuesta])
def listar_assets(
    variante_id: int = Query(...), db: Session = Depends(get_db)
) -> list[ActivoRespuesta]:
    activos = service.listar_assets(db, variante_id)
    return [ActivoRespuesta.from_modelo(a, url) for a, url in activos]


@router.post("", response_model=ActivoRespuesta, status_code=status.HTTP_201_CREATED)
def subir_asset(
    variante_id: int = Form(...),
    tipo: TipoActivo = Form(...),
    archivo: UploadFile = File(...),
    usuario=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ActivoRespuesta:
    contenido = archivo.file.read()
    activo, url = service.subir_asset(db, variante_id, tipo, contenido, archivo.content_type, usuario.id)
    return ActivoRespuesta.from_modelo(activo, url)


@router.put("/{activo_id}/anclajes", response_model=ActivoRespuesta)
def guardar_anclajes(
    activo_id: int, datos: AnclajesActualizar, db: Session = Depends(get_db)
) -> ActivoRespuesta:
    activo, url = service.guardar_anclajes(db, activo_id, datos)
    return ActivoRespuesta.from_modelo(activo, url)


@router.put("/{activo_id}/validar", response_model=ActivoRespuesta)
def validar_asset(activo_id: int, db: Session = Depends(get_db)) -> ActivoRespuesta:
    activo, url = service.validar_asset(db, activo_id)
    return ActivoRespuesta.from_modelo(activo, url)


# ---- Uso del probador (cliente) ----------------------------------------------


@uso_router.get("/variante/{variante_id}/assets", response_model=AssetsVarianteRespuesta)
def obtener_assets_uso(
    variante_id: int, usuario=Depends(get_current_user), db: Session = Depends(get_db)
) -> AssetsVarianteRespuesta:
    overlay, overlay_url, flatlay, flatlay_url = service.obtener_assets_uso(db, variante_id)
    return AssetsVarianteRespuesta(
        overlay=ActivoRespuesta.from_modelo(overlay, overlay_url),
        flatlay=ActivoRespuesta.from_modelo(flatlay, flatlay_url) if flatlay else None,
    )


@uso_router.post("/generar", response_model=GeneracionIniciadaRespuesta, status_code=status.HTTP_202_ACCEPTED)
def iniciar_generacion(
    background_tasks: BackgroundTasks,
    variante_id: int = Form(...),
    archivo: UploadFile = File(...),  # una sola imagen por petición: un único UploadFile, no una lista
    usuario=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GeneracionIniciadaRespuesta:
    contenido = archivo.file.read()
    generacion, desde_cache = service.iniciar_generacion(
        db, usuario.id, variante_id, contenido, archivo.content_type, background_tasks
    )
    return GeneracionIniciadaRespuesta(
        id=generacion.id, estado=generacion.estado, url_resultado=generacion.url_resultado, desde_cache=desde_cache
    )


@uso_router.get("/generar/{generacion_id}", response_model=GeneracionEstadoRespuesta)
def consultar_generacion(
    generacion_id: int, usuario=Depends(get_current_user), db: Session = Depends(get_db)
) -> GeneracionEstadoRespuesta:
    generacion = service.consultar_generacion(db, usuario.id, generacion_id)
    return GeneracionEstadoRespuesta.model_validate(generacion)


@uso_router.post("/sesion", response_model=SesionRespuesta, status_code=status.HTTP_201_CREATED)
def registrar_sesion(
    datos: SesionCrear, usuario=Depends(get_current_user), db: Session = Depends(get_db)
) -> SesionRespuesta:
    sesion = service.registrar_sesion(db, usuario.id, datos)
    return SesionRespuesta.model_validate(sesion)


@uso_router.post("/talla", response_model=TallaRecomendadaRespuesta)
def recomendar_talla(
    datos: TallaRequest, usuario=Depends(get_current_user), db: Session = Depends(get_db)
) -> TallaRecomendadaRespuesta:
    return service.recomendar_talla(db, datos)


routers = [router, uso_router]
