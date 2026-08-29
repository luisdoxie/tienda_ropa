from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NoEncontradoError
from app.probador.models import ActivoProbador


class ActivoRepository:
    """No hereda de CRUDBase: activo_probador no tiene borrado lógico (no
    hay endpoint de borrado en el enunciado; un asset rechazado se
    conserva como historial y se puede subir otro para la misma
    variante+tipo, gracias al índice único parcial `WHERE estado <> 'rechazado'`)."""

    def listar_por_variante(self, db: Session, variante_id: int) -> list[ActivoProbador]:
        return list(
            db.scalars(
                select(ActivoProbador)
                .where(ActivoProbador.variante_id == variante_id)
                .order_by(ActivoProbador.creado_en.desc())
            )
        )

    def obtener(self, db: Session, activo_id: int) -> ActivoProbador:
        activo = db.get(ActivoProbador, activo_id)
        if activo is None:
            raise NoEncontradoError("Asset de probador no encontrado")
        return activo

    def crear(
        self,
        db: Session,
        variante_id: int,
        tipo: str,
        public_id: str,
        ancho_px: int,
        alto_px: int,
        creado_por: int | None,
    ) -> ActivoProbador:
        activo = ActivoProbador(
            variante_id=variante_id,
            tipo=tipo,
            url=public_id,
            ancho_px=ancho_px,
            alto_px=alto_px,
            estado="pendiente",
            creado_por=creado_por,
        )
        db.add(activo)
        db.commit()
        db.refresh(activo)
        return activo

    def guardar_anclajes(self, db: Session, activo: ActivoProbador, anclajes: dict) -> ActivoProbador:
        activo.anclajes = anclajes
        db.commit()
        db.refresh(activo)
        return activo

    def marcar_validado(self, db: Session, activo: ActivoProbador) -> ActivoProbador:
        activo.estado = "validado"
        db.commit()
        db.refresh(activo)
        return activo
