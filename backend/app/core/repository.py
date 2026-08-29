from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.models import Notificacion


class NotificacionRepository:
    """Sin `activo`: una notificación no se desactiva, se marca leída (fuera
    de alcance de esta etapa) o simplemente se acumula."""

    def crear(
        self,
        db: Session,
        usuario_id: int,
        titulo: str,
        mensaje: str | None,
        tipo: str | None,
        referencia_id: int | None,
    ) -> Notificacion:
        notificacion = Notificacion(
            usuario_id=usuario_id, titulo=titulo, mensaje=mensaje, tipo=tipo, referencia_id=referencia_id
        )
        db.add(notificacion)
        db.flush()
        return notificacion

    def listar_por_usuario(self, db: Session, usuario_id: int) -> list[Notificacion]:
        return list(
            db.scalars(
                select(Notificacion)
                .where(Notificacion.usuario_id == usuario_id)
                .order_by(Notificacion.creado_en.desc())
            )
        )
