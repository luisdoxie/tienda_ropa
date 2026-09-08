from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.rate_limit import limiter
from app.core.security import get_current_user_opcional, require_permission
from app.inteligencia import service
from app.inteligencia.schemas import (
    EventoCrear,
    RecomendacionesRespuesta,
    ReporteVozRequest,
    ReporteVozRespuesta,
    VozRequest,
    VozRespuesta,
)

router = APIRouter(prefix="/api/v1/ia", tags=["inteligencia"])


@router.post("/voz", response_model=VozRespuesta)
@limiter.limit("15/minute")
def buscar_por_voz(
    request: Request,
    datos: VozRequest,
    usuario=Depends(get_current_user_opcional),
    db: Session = Depends(get_db),
) -> VozRespuesta:
    return service.buscar_por_voz(db, datos.texto, usuario)


@router.post("/recomendaciones", response_model=RecomendacionesRespuesta)
@limiter.limit("20/minute")
def obtener_recomendaciones(
    request: Request,
    excluir_producto_id: int | None = None,
    usuario=Depends(get_current_user_opcional),
    db: Session = Depends(get_db),
) -> RecomendacionesRespuesta:
    return service.obtener_recomendaciones(db, usuario, excluir_producto_id)


@router.post("/eventos", status_code=status.HTTP_201_CREATED)
@limiter.limit("60/minute")
def registrar_evento(
    request: Request,
    datos: EventoCrear,
    usuario=Depends(get_current_user_opcional),
    db: Session = Depends(get_db),
) -> dict:
    service.registrar_evento(db, datos, usuario)
    return {"registrado": True}


@router.post(
    "/reporte-voz", response_model=ReporteVozRespuesta, dependencies=[Depends(require_permission("reportes.ver"))]
)
@limiter.limit("15/minute")
def generar_reporte_por_voz(request: Request, datos: ReporteVozRequest, db: Session = Depends(get_db)) -> ReporteVozRespuesta:
    return service.generar_reporte_por_voz(db, datos.texto)


routers = [router]
