from __future__ import annotations

import datetime as dt

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.deps import ParametrosPaginacion
from app.core.exceptions import NoEncontradoError
from app.ventas.models import (
    Carrito,
    CarritoDetalle,
    Devolucion,
    DevolucionDetalle,
    EstadoVenta,
    Promocion,
    PromocionAlcance,
    Venta,
)


class EstadoVentaRepository:
    def obtener_por_codigo(self, db: Session, codigo: str) -> EstadoVenta:
        estado = db.scalar(select(EstadoVenta).where(EstadoVenta.codigo == codigo))
        if estado is None:
            raise NoEncontradoError(f"Estado de venta '{codigo}' no encontrado")
        return estado

    def obtener(self, db: Session, estado_id: int) -> EstadoVenta:
        estado = db.get(EstadoVenta, estado_id)
        if estado is None:
            raise NoEncontradoError("Estado de venta no encontrado")
        return estado

    def mapa_codigos_por_id(self, db: Session) -> dict[int, str]:
        return {estado.id: estado.codigo for estado in db.scalars(select(EstadoVenta))}


class VentaRepository:
    """No hereda de CRUDBase: `venta` no tiene columna `activo` y crear()
    maneja cabecera + detalle como parte de la misma operación (ver
    ventas.service.registrar_venta)."""

    def _consulta_base(self):
        return select(Venta).options(selectinload(Venta.detalle))

    def obtener(self, db: Session, venta_id: int) -> Venta:
        venta = db.scalar(self._consulta_base().where(Venta.id == venta_id))
        if venta is None:
            raise NoEncontradoError("Venta no encontrada")
        return venta

    def obtener_por_codigo(self, db: Session, codigo: str) -> Venta | None:
        return db.scalar(self._consulta_base().where(Venta.codigo == codigo))

    def listar_por_cliente(self, db: Session, cliente_id: int) -> list[Venta]:
        return list(
            db.scalars(self._consulta_base().where(Venta.cliente_id == cliente_id).order_by(Venta.fecha.desc()))
        )

    def listar_por_sucursal(self, db: Session, sucursal_id: int) -> list[Venta]:
        return list(
            db.scalars(self._consulta_base().where(Venta.sucursal_id == sucursal_id).order_by(Venta.fecha.desc()))
        )

    def crear(self, db: Session, venta: Venta) -> Venta:
        db.add(venta)
        db.flush()
        return venta


class PromocionRepository:
    def _consulta_base(self):
        return select(Promocion).options(selectinload(Promocion.alcances))

    def obtener(self, db: Session, promocion_id: int) -> Promocion:
        promocion = db.scalar(self._consulta_base().where(Promocion.id == promocion_id))
        if promocion is None:
            raise NoEncontradoError("Promoción no encontrada")
        return promocion

    def listar(self, db: Session, paginacion: ParametrosPaginacion) -> list[Promocion]:
        consulta = self._consulta_base().order_by(Promocion.id.desc()).offset(paginacion.offset).limit(
            paginacion.tamanio
        )
        return list(db.scalars(consulta))

    def crear(self, db: Session, promocion: Promocion) -> Promocion:
        db.add(promocion)
        db.flush()
        return promocion

    def listar_vigentes_para(
        self, db: Session, *, producto_id: int, categoria_id: int, temporada_id: int | None, hoy: dt.date
    ) -> list[Promocion]:
        """Promociones activas y vigentes hoy cuyo `promocion_alcance` matchea
        este producto (por producto_id, categoria_id o temporada_id)."""
        condiciones = [PromocionAlcance.producto_id == producto_id, PromocionAlcance.categoria_id == categoria_id]
        if temporada_id is not None:
            condiciones.append(PromocionAlcance.temporada_id == temporada_id)

        consulta = (
            select(Promocion)
            .join(PromocionAlcance, PromocionAlcance.promocion_id == Promocion.id)
            .where(
                Promocion.activo.is_(True),
                Promocion.fecha_inicio <= hoy,
                Promocion.fecha_fin >= hoy,
                or_(*condiciones),
            )
            .distinct()
        )
        return list(db.scalars(consulta))


class CarritoRepository:
    def _consulta_base(self):
        return select(Carrito).options(selectinload(Carrito.detalle))

    def obtener_por_cliente(self, db: Session, cliente_id: int) -> Carrito | None:
        return db.scalar(self._consulta_base().where(Carrito.cliente_id == cliente_id))

    def obtener_o_crear(self, db: Session, cliente_id: int) -> Carrito:
        carrito = self.obtener_por_cliente(db, cliente_id)
        if carrito is None:
            carrito = Carrito(cliente_id=cliente_id)
            db.add(carrito)
            db.flush()
        return carrito

    def obtener_linea(self, db: Session, carrito_id: int, variante_id: int) -> CarritoDetalle | None:
        return db.scalar(
            select(CarritoDetalle).where(
                CarritoDetalle.carrito_id == carrito_id, CarritoDetalle.variante_id == variante_id
            )
        )

    def vaciar(self, db: Session, carrito: Carrito) -> None:
        for linea in list(carrito.detalle):
            db.delete(linea)
        db.flush()


class DevolucionRepository:
    def _consulta_base(self):
        return select(Devolucion).options(selectinload(Devolucion.detalle))

    def obtener(self, db: Session, devolucion_id: int) -> Devolucion:
        devolucion = db.scalar(self._consulta_base().where(Devolucion.id == devolucion_id))
        if devolucion is None:
            raise NoEncontradoError("Devolución no encontrada")
        return devolucion

    def crear(self, db: Session, devolucion: Devolucion) -> Devolucion:
        db.add(devolucion)
        db.flush()
        return devolucion

    def cantidad_devuelta(self, db: Session, venta_detalle_id: int) -> int:
        """Suma de todo lo ya devuelto de esa línea, en TODAS las
        devoluciones anteriores (no solo la que se está creando ahora):
        evita devolver más de lo que se vendió a través de varias
        devoluciones parciales."""
        total = db.scalar(
            select(func.coalesce(func.sum(DevolucionDetalle.cantidad), 0)).where(
                DevolucionDetalle.venta_detalle_id == venta_detalle_id
            )
        )
        return int(total or 0)
