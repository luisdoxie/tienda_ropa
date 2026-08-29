from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core import service
from app.core.database import get_db
from app.core.schemas import NotificacionRespuesta
from app.core.security import get_current_user

router = APIRouter(prefix="/api/v1/notificaciones", tags=["notificaciones"])


@router.get("", response_model=list[NotificacionRespuesta])
def listar_notificaciones(
    usuario=Depends(get_current_user), db: Session = Depends(get_db)
) -> list[NotificacionRespuesta]:
    return list(service.listar_notificaciones(db, usuario.id))


routers = [router]
