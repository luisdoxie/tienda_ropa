from __future__ import annotations

import datetime as dt
from decimal import Decimal

from pydantic import BaseModel

from app.inventario.schemas import ConsolidadoRespuesta, ValuacionRespuesta

# ---- Ventas ---------------------------------------------------------------------


class FilaVentasDetalle(BaseModel):
    """Una fila de vw_ventas_detalle (ventas/repository.py)."""

    venta_id: int
    codigo: str
    canal: str
    fecha: dt.datetime
    sucursal_id: int
    sucursal: str
    producto_id: int
    producto: str
    categoria_id: int
    categoria: str
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal
    costo_unitario: Decimal | None
    margen: Decimal


class ResumenVentas(BaseModel):
    transacciones: int
    total_ventas: Decimal
    ticket_promedio: Decimal
    margen_bruto: Decimal


class FilaTopProducto(BaseModel):
    producto_id: int
    producto: str
    cantidad_vendida: int
    total_vendido: Decimal


class FilaVentasPorCanal(BaseModel):
    canal: str
    transacciones: int
    total_ventas: Decimal


class FilaVentasPorSucursal(BaseModel):
    sucursal_id: int
    sucursal: str
    transacciones: int
    total_ventas: Decimal


class ReporteVentasRespuesta(BaseModel):
    resumen: ResumenVentas
    top_productos: list[FilaTopProducto]
    por_canal: list[FilaVentasPorCanal]
    por_sucursal: list[FilaVentasPorSucursal]
    detalle: list[FilaVentasDetalle]


# ---- Inventario -------------------------------------------------------------------


class ReporteInventarioRespuesta(BaseModel):
    consolidado: list[ConsolidadoRespuesta]
    alertas: list[ConsolidadoRespuesta]
    valuacion: list[ValuacionRespuesta]


# ---- Reservas ---------------------------------------------------------------------


class FilaReservasPorEstado(BaseModel):
    codigo: str
    nombre: str
    cantidad: int


class ReporteReservasRespuesta(BaseModel):
    por_estado: list[FilaReservasPorEstado]
    tasa_conversion: float


# ---- Probador -----------------------------------------------------------------------


class FilaUsoProbador(BaseModel):
    modo: str
    cantidad: int


# ---- Dashboard ---------------------------------------------------------------------


class DashboardRespuesta(BaseModel):
    """Los 12 indicadores del enunciado, livianos (sin el detalle fila por
    fila de ventas -- eso es solo para /reportes/ventas)."""

    desde: dt.date
    hasta: dt.date
    ventas_del_periodo: Decimal
    transacciones: int
    ticket_promedio: Decimal
    margen_bruto: Decimal
    top_productos: list[FilaTopProducto]
    ventas_por_canal: list[FilaVentasPorCanal]
    ventas_por_sucursal: list[FilaVentasPorSucursal]
    valor_inventario_total: Decimal
    variantes_bajo_minimo: int
    reservas_por_estado: list[FilaReservasPorEstado]
    tasa_conversion_reservas: float
    uso_probador: list[FilaUsoProbador]
