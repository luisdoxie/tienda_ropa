from sqlalchemy.orm import Session

from app.core.models import Notificacion
from app.core.repository import NotificacionRepository

notificacion_repo = NotificacionRepository()


def crear_notificacion(
    db: Session,
    usuario_id: int,
    titulo: str,
    mensaje: str | None = None,
    tipo: str | None = None,
    referencia_id: int | None = None,
    commit: bool = True,
) -> Notificacion:
    """`commit=False`: ver el comentario en inventario.service.registrar_movimiento
    (lo usa reservas.service.crear_reserva, que notifica a varios empleados
    como parte de la misma transacción)."""
    notificacion = notificacion_repo.crear(db, usuario_id, titulo, mensaje, tipo, referencia_id)
    if commit:
        db.commit()
        db.refresh(notificacion)
    return notificacion


def listar_notificaciones(db: Session, usuario_id: int) -> list[Notificacion]:
    return notificacion_repo.listar_por_usuario(db, usuario_id)
