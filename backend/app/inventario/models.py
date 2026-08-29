from __future__ import annotations

import datetime as dt
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Computed,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Stock(Base):
    __tablename__ = "stock"
    __table_args__ = (
        UniqueConstraint("variante_id", "sucursal_id", name="uq_stock_variante_sucursal"),
        CheckConstraint("cantidad_fisica >= 0", name="ck_stock_cantidad_fisica"),
        CheckConstraint("cantidad_reservada >= 0", name="ck_stock_cantidad_reservada"),
        CheckConstraint("cantidad_reservada <= cantidad_fisica", name="ck_stock_reservada_no_supera_fisica"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    variante_id: Mapped[int] = mapped_column(ForeignKey("producto_variante.id"), nullable=False)
    sucursal_id: Mapped[int] = mapped_column(ForeignKey("sucursal.id"), nullable=False)
    cantidad_fisica: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cantidad_reservada: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Columna generada por la base: nunca se escribe desde el código.
    cantidad_disponible: Mapped[int] = mapped_column(
        Integer, Computed("cantidad_fisica - cantidad_reservada", persisted=True)
    )
    stock_minimo: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    stock_maximo: Mapped[int | None] = mapped_column(Integer)
    costo_promedio: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False, default=0)
    actualizado_en: Mapped[dt.datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )


class TipoMovimiento(Base):
    __tablename__ = "tipo_movimiento"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(25), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(60), nullable=False)
    signo: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    afecta_costo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    __table_args__ = (CheckConstraint("signo IN (-1, 1)", name="ck_tipo_movimiento_signo"),)


# Libro inmutable: nunca se edita ni se borra desde el código. El stock es
# la suma de sus movimientos (ver service.registrar_movimiento).
class MovimientoInventario(Base):
    __tablename__ = "movimiento_inventario"
    __table_args__ = (CheckConstraint("cantidad <> 0", name="ck_movimiento_cantidad"),)

    # BigInteger en Postgres (BIGSERIAL, como pide el esquema); en SQLite
    # (tests) se compila a INTEGER, el único tipo que ahí se autoincrementa
    # como alias del rowid al ser primary key.
    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True)
    variante_id: Mapped[int] = mapped_column(ForeignKey("producto_variante.id"), nullable=False)
    sucursal_id: Mapped[int] = mapped_column(ForeignKey("sucursal.id"), nullable=False)
    tipo_movimiento_id: Mapped[int] = mapped_column(ForeignKey("tipo_movimiento.id"), nullable=False)
    # Ya incluye el signo del tipo de movimiento (positivo entrada, negativo
    # salida): saldo_post de cada fila es la suma acumulada de esta columna.
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    costo_unitario: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    costo_promedio_post: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    saldo_post: Mapped[int] = mapped_column(Integer, nullable=False)
    referencia_tipo: Mapped[str | None] = mapped_column(String(25))
    referencia_id: Mapped[int | None]
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"))
    observacion: Mapped[str | None] = mapped_column(String(300))
    creado_en: Mapped[dt.datetime] = mapped_column(server_default=func.now())


class Transferencia(Base):
    __tablename__ = "transferencia"
    __table_args__ = (
        CheckConstraint("sucursal_origen_id <> sucursal_destino_id", name="ck_transferencia_sucursales"),
        CheckConstraint(
            "estado IN ('pendiente','en_transito','recibida','anulada')", name="ck_transferencia_estado"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    sucursal_origen_id: Mapped[int] = mapped_column(ForeignKey("sucursal.id"), nullable=False)
    sucursal_destino_id: Mapped[int] = mapped_column(ForeignKey("sucursal.id"), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="pendiente")
    fecha_envio: Mapped[dt.datetime | None]
    fecha_recepcion: Mapped[dt.datetime | None]
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"))

    detalle: Mapped[list["TransferenciaDetalle"]] = relationship(
        back_populates="transferencia", order_by="TransferenciaDetalle.id"
    )


class TransferenciaDetalle(Base):
    __tablename__ = "transferencia_detalle"
    __table_args__ = (CheckConstraint("cantidad > 0", name="ck_transferencia_detalle_cantidad"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    transferencia_id: Mapped[int] = mapped_column(
        ForeignKey("transferencia.id", ondelete="CASCADE"), nullable=False
    )
    variante_id: Mapped[int] = mapped_column(ForeignKey("producto_variante.id"), nullable=False)
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)

    transferencia: Mapped[Transferencia] = relationship(back_populates="detalle")
