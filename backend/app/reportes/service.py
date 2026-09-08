from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.deps import ParametrosPeriodo
from app.inventario import service as inventario_service
from app.probador import service as probador_service
from app.reportes.schemas import (
    DashboardRespuesta,
    FilaReservasPorEstado,
    FilaTopProducto,
    FilaUsoProbador,
    FilaVentasDetalle,
    FilaVentasPorCanal,
    FilaVentasPorSucursal,
    ReporteInventarioRespuesta,
    ReporteReservasRespuesta,
    ReporteVentasRespuesta,
    ResumenVentas,
)
from app.reservas import service as reservas_service
from app.ventas import service as ventas_service

_CERO = Decimal("0")


def _ticket_promedio(total_ventas: Decimal, transacciones: int) -> Decimal:
    if transacciones == 0:
        return _CERO
    return (total_ventas / transacciones).quantize(Decimal("0.01"))


def _tasa_conversion(por_estado: list[dict], ventas_con_reserva: int) -> float:
    total_reservas = sum(fila["cantidad"] for fila in por_estado)
    if total_reservas == 0:
        return 0.0
    return round(ventas_con_reserva / total_reservas, 4)


def reporte_ventas(
    db: Session,
    periodo: ParametrosPeriodo,
    sucursal_id: int | None = None,
    categoria_id: int | None = None,
    canal: str | None = None,
) -> ReporteVentasRespuesta:
    resumen_dict = ventas_service.reporte_ventas_resumen(db, periodo, sucursal_id, categoria_id, canal)
    resumen = ResumenVentas(
        transacciones=resumen_dict["transacciones"],
        total_ventas=resumen_dict["total_ventas"],
        margen_bruto=resumen_dict["margen_bruto"],
        ticket_promedio=_ticket_promedio(resumen_dict["total_ventas"], resumen_dict["transacciones"]),
    )
    return ReporteVentasRespuesta(
        resumen=resumen,
        top_productos=[
            FilaTopProducto(**fila)
            for fila in ventas_service.reporte_ventas_top_productos(db, periodo, sucursal_id, categoria_id, canal)
        ],
        por_canal=[
            FilaVentasPorCanal(**fila)
            for fila in ventas_service.reporte_ventas_por_canal(db, periodo, sucursal_id, categoria_id)
        ],
        por_sucursal=[
            FilaVentasPorSucursal(**fila)
            for fila in ventas_service.reporte_ventas_por_sucursal(db, periodo, categoria_id, canal)
        ],
        detalle=[
            FilaVentasDetalle(**fila)
            for fila in ventas_service.reporte_ventas_detalle(db, periodo, sucursal_id, categoria_id, canal)
        ],
    )


def reporte_inventario(db: Session, sucursal_id: int | None = None) -> ReporteInventarioRespuesta:
    return ReporteInventarioRespuesta(
        consolidado=inventario_service.listar_consolidado(db, sucursal_id),
        alertas=inventario_service.listar_alertas(db, sucursal_id),
        valuacion=inventario_service.listar_valuacion(db, sucursal_id),
    )


def reporte_reservas(
    db: Session, periodo: ParametrosPeriodo, sucursal_id: int | None = None
) -> ReporteReservasRespuesta:
    por_estado = reservas_service.reporte_reservas_por_estado(db, periodo, sucursal_id)
    ventas_con_reserva = ventas_service.contar_ventas_con_reserva(db, periodo, sucursal_id)
    return ReporteReservasRespuesta(
        por_estado=[FilaReservasPorEstado(**fila) for fila in por_estado],
        tasa_conversion=_tasa_conversion(por_estado, ventas_con_reserva),
    )


def reporte_dashboard(db: Session, periodo: ParametrosPeriodo, sucursal_id: int | None = None) -> DashboardRespuesta:
    resumen_dict = ventas_service.reporte_ventas_resumen(db, periodo, sucursal_id)
    top_productos = ventas_service.reporte_ventas_top_productos(db, periodo, sucursal_id, limite=5)
    por_canal = ventas_service.reporte_ventas_por_canal(db, periodo, sucursal_id)
    por_sucursal = ventas_service.reporte_ventas_por_sucursal(db, periodo)

    alertas = inventario_service.listar_alertas(db, sucursal_id)
    valuacion = inventario_service.listar_valuacion(db, sucursal_id)
    valor_inventario_total = sum((fila["valor_total"] for fila in valuacion), _CERO)

    por_estado = reservas_service.reporte_reservas_por_estado(db, periodo, sucursal_id)
    ventas_con_reserva = ventas_service.contar_ventas_con_reserva(db, periodo, sucursal_id)

    uso_probador = probador_service.reporte_uso_probador(db, periodo)

    return DashboardRespuesta(
        desde=periodo.desde,
        hasta=periodo.hasta,
        ventas_del_periodo=resumen_dict["total_ventas"],
        transacciones=resumen_dict["transacciones"],
        ticket_promedio=_ticket_promedio(resumen_dict["total_ventas"], resumen_dict["transacciones"]),
        margen_bruto=resumen_dict["margen_bruto"],
        top_productos=[FilaTopProducto(**fila) for fila in top_productos],
        ventas_por_canal=[FilaVentasPorCanal(**fila) for fila in por_canal],
        ventas_por_sucursal=[FilaVentasPorSucursal(**fila) for fila in por_sucursal],
        valor_inventario_total=valor_inventario_total,
        variantes_bajo_minimo=len(alertas),
        reservas_por_estado=[FilaReservasPorEstado(**fila) for fila in por_estado],
        tasa_conversion_reservas=_tasa_conversion(por_estado, ventas_con_reserva),
        uso_probador=[FilaUsoProbador(**fila) for fila in uso_probador],
    )
