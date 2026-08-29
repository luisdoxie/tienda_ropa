from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_permission
from app.probador import service
from app.probador.schemas import ActivoRespuesta, AnclajesActualizar, TipoActivo

PERMISO_PROBADOR = "probador.gestionar"
admin_requerido = Depends(require_permission(PERMISO_PROBADOR))

router = APIRouter(prefix="/api/v1/probador/assets", tags=["probador"], dependencies=[admin_requerido])


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


routers = [router]
