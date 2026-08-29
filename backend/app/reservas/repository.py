import datetime as dt

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import NoEncontradoError
from app.reservas.models import EstadoReserva, Reserva


class EstadoReservaRepository:
    def obtener_por_codigo(self, db: Session, codigo: str) -> EstadoReserva:
        estado = db.scalar(select(EstadoReserva).where(EstadoReserva.codigo == codigo))
        if estado is None:
            raise NoEncontradoError(f"Estado de reserva '{codigo}' no encontrado")
        return estado

    def obtener(self, db: Session, estado_id: int) -> EstadoReserva:
        estado = db.get(EstadoReserva, estado_id)
        if estado is None:
            raise NoEncontradoError("Estado de reserva no encontrado")
        return estado

    def mapa_codigos_por_id(self, db: Session) -> dict[int, str]:
        return {estado.id: estado.codigo for estado in db.scalars(select(EstadoReserva))}


class ReservaRepository:
    """No hereda de CRUDBase: `reserva` no tiene columna `activo`, su ciclo
    de vida es la máquina de estados de reservas.service, y crear() maneja
    detalle + historial como parte de la misma operación."""

    def _consulta_base(self):
        return select(Reserva).options(selectinload(Reserva.detalle), selectinload(Reserva.historial))

    def obtener_por_codigo(self, db: Session, codigo: str) -> Reserva | None:
        return db.scalar(self._consulta_base().where(Reserva.codigo == codigo))

    def obtener(self, db: Session, reserva_id: int) -> Reserva:
        reserva = db.scalar(self._consulta_base().where(Reserva.id == reserva_id))
        if reserva is None:
            raise NoEncontradoError("Reserva no encontrada")
        return reserva

    def listar_por_cliente(self, db: Session, cliente_id: int) -> list[Reserva]:
        return list(
            db.scalars(
                self._consulta_base().where(Reserva.cliente_id == cliente_id).order_by(Reserva.creado_en.desc())
            )
        )

    def listar_por_sucursal(self, db: Session, sucursal_id: int) -> list[Reserva]:
        return list(
            db.scalars(
                self._consulta_base().where(Reserva.sucursal_id == sucursal_id).order_by(Reserva.creado_en.desc())
            )
        )

    def listar_vencidas(self, db: Session, ahora: dt.datetime, estados_ids: list[int]) -> list[Reserva]:
        return list(
            db.scalars(
                self._consulta_base().where(
                    Reserva.fecha_expiracion < ahora,
                    Reserva.estado_id.in_(estados_ids),
                )
            )
        )

    def crear(self, db: Session, reserva: Reserva) -> Reserva:
        db.add(reserva)
        db.flush()
        return reserva
