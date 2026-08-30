from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NoEncontradoError
from app.pagos.models import EstadoPago, MetodoPago, Pago, TransaccionPasarela


class MetodoPagoRepository:
    def obtener_por_codigo(self, db: Session, codigo: str) -> MetodoPago:
        metodo = db.scalar(select(MetodoPago).where(MetodoPago.codigo == codigo))
        if metodo is None or not metodo.activo:
            raise NoEncontradoError(f"Método de pago '{codigo}' no encontrado")
        return metodo


class EstadoPagoRepository:
    def obtener_por_codigo(self, db: Session, codigo: str) -> EstadoPago:
        estado = db.scalar(select(EstadoPago).where(EstadoPago.codigo == codigo))
        if estado is None:
            raise NoEncontradoError(f"Estado de pago '{codigo}' no encontrado")
        return estado

    def obtener(self, db: Session, estado_id: int) -> EstadoPago:
        estado = db.get(EstadoPago, estado_id)
        if estado is None:
            raise NoEncontradoError("Estado de pago no encontrado")
        return estado

    def mapa_codigos_por_id(self, db: Session) -> dict[int, str]:
        return {estado.id: estado.codigo for estado in db.scalars(select(EstadoPago))}


class PagoRepository:
    def obtener(self, db: Session, pago_id: int) -> Pago:
        pago = db.get(Pago, pago_id)
        if pago is None:
            raise NoEncontradoError("Pago no encontrado")
        return pago

    def listar_por_venta(self, db: Session, venta_id: int) -> list[Pago]:
        return list(db.scalars(select(Pago).where(Pago.venta_id == venta_id).order_by(Pago.fecha.desc())))

    def crear(self, db: Session, pago: Pago) -> Pago:
        db.add(pago)
        db.flush()
        return pago


class TransaccionPasarelaRepository:
    def crear(self, db: Session, transaccion: TransaccionPasarela) -> TransaccionPasarela:
        db.add(transaccion)
        db.flush()
        return transaccion

    def obtener_por_id_transaccion(self, db: Session, pasarela: str, id_transaccion: str) -> TransaccionPasarela | None:
        """Busca la transacción MÁS VIEJA con este id (la que
        `iniciar_pago` dejó como registro original): así el webhook
        encuentra a qué `pago` corresponde, sin importar cuántas filas de
        evidencia ya se hayan acumulado para esa misma transacción."""
        return db.scalar(
            select(TransaccionPasarela)
            .where(TransaccionPasarela.pasarela == pasarela, TransaccionPasarela.id_transaccion == id_transaccion)
            .order_by(TransaccionPasarela.creado_en.asc())
            .limit(1)
        )
