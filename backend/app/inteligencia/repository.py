from sqlalchemy.orm import Session

from app.inteligencia.models import ConsultaVoz


class ConsultaVozRepository:
    """Sin `activo`: es un log de auditoría, nunca se desactiva ni se lista
    de vuelta desde una pantalla administrable (igual criterio que
    NotificacionRepository en core/repository.py)."""

    def crear(
        self,
        db: Session,
        cliente_id: int | None,
        texto_transcrito: str,
        filtros_json: dict | None,
        cantidad_resultados: int,
    ) -> ConsultaVoz:
        consulta = ConsultaVoz(
            cliente_id=cliente_id,
            texto_transcrito=texto_transcrito,
            filtros_json=filtros_json,
            cantidad_resultados=cantidad_resultados,
        )
        db.add(consulta)
        db.commit()
        db.refresh(consulta)
        return consulta
