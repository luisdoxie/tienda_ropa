import { FilaConsolidado, FilaValuacion } from './inventario.models';

// ---- Ventas -----------------------------------------------------------------------

/** Una fila de vw_ventas_detalle (backend/app/ventas/repository.py). */
export interface FilaVentasDetalle {
  venta_id: number;
  codigo: string;
  canal: string;
  fecha: string;
  sucursal_id: number;
  sucursal: string;
  producto_id: number;
  producto: string;
  categoria_id: number;
  categoria: string;
  cantidad: number;
  precio_unitario: number;
  subtotal: number;
  costo_unitario: number | null;
  margen: number;
}

export interface ResumenVentas {
  transacciones: number;
  total_ventas: number;
  ticket_promedio: number;
  margen_bruto: number;
}

export interface FilaTopProducto {
  producto_id: number;
  producto: string;
  cantidad_vendida: number;
  total_vendido: number;
}

export interface FilaVentasPorCanal {
  canal: string;
  transacciones: number;
  total_ventas: number;
}

export interface FilaVentasPorSucursal {
  sucursal_id: number;
  sucursal: string;
  transacciones: number;
  total_ventas: number;
}

export interface ReporteVentas {
  resumen: ResumenVentas;
  top_productos: FilaTopProducto[];
  por_canal: FilaVentasPorCanal[];
  por_sucursal: FilaVentasPorSucursal[];
  detalle: FilaVentasDetalle[];
}

// ---- Inventario -------------------------------------------------------------------

export interface ReporteInventario {
  consolidado: FilaConsolidado[];
  alertas: FilaConsolidado[];
  valuacion: FilaValuacion[];
}

// ---- Reservas ---------------------------------------------------------------------

export interface FilaReservasPorEstado {
  codigo: string;
  nombre: string;
  cantidad: number;
}

export interface ReporteReservas {
  por_estado: FilaReservasPorEstado[];
  tasa_conversion: number;
}

// ---- Probador -----------------------------------------------------------------------

export interface FilaUsoProbador {
  modo: string;
  cantidad: number;
}

// ---- Dashboard ---------------------------------------------------------------------

export interface DashboardReportes {
  desde: string;
  hasta: string;
  ventas_del_periodo: number;
  transacciones: number;
  ticket_promedio: number;
  margen_bruto: number;
  top_productos: FilaTopProducto[];
  ventas_por_canal: FilaVentasPorCanal[];
  ventas_por_sucursal: FilaVentasPorSucursal[];
  valor_inventario_total: number;
  variantes_bajo_minimo: number;
  reservas_por_estado: FilaReservasPorEstado[];
  tasa_conversion_reservas: number;
  uso_probador: FilaUsoProbador[];
}

// ---- Reporte por voz ----------------------------------------------------------------

export interface ReporteVozRespuesta {
  tipo_reporte: string;
  filtros_aplicados: Record<string, unknown>;
  resultado: Record<string, unknown>;
}
