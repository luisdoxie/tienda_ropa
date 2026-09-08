from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.rate_limit import limiter
from app.core.security import get_current_user_opcional
from app.inteligencia import service
from app.inteligencia.schemas import VozRequest, VozRespuesta

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


routers = [router]
