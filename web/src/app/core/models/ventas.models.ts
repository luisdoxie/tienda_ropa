export type EstadoVenta = 'pendiente_pago' | 'pagada' | 'entregada' | 'anulada';
export type CanalVenta = 'digital' | 'presencial';
export type TipoPromocion = 'porcentaje' | 'monto';

export interface VentaDetalleLinea {
  variante_id: number;
  cantidad: number;
}

export interface VentaPresencialCrear {
  sucursal_id: number;
  detalle?: VentaDetalleLinea[];
  reserva_id?: number | null;
  cliente_id?: number | null;
}

export interface VentaDetalle {
  id: number;
  variante_id: number;
  cantidad: number;
  precio_unitario: number;
  descuento_unitario: number;
  costo_unitario: number | null;
  subtotal: number;
}

export interface Venta {
  id: number;
  codigo: string;
  canal: CanalVenta;
  cliente_id: number | null;
  sucursal_id: number;
  cajero_id: number | null;
  reserva_id: number | null;
  estado: EstadoVenta;
  fecha: string;
  subtotal: number;
  descuento: number;
  costo_envio: number;
  total: number;
  detalle: VentaDetalle[];
}

export interface DevolucionDetalleCrear {
  venta_detalle_id: number;
  cantidad: number;
}

export interface DevolucionCrear {
  venta_id: number;
  motivo?: string | null;
  detalle: DevolucionDetalleCrear[];
}

export interface DevolucionDetalle {
  id: number;
  venta_detalle_id: number;
  cantidad: number;
}

export interface Devolucion {
  id: number;
  codigo: string;
  venta_id: number;
  fecha: string;
  motivo: string | null;
  estado: 'pendiente' | 'aprobada' | 'rechazada';
  usuario_id: number | null;
  detalle: DevolucionDetalle[];
}

export interface PromocionAlcance {
  id: number;
  producto_id: number | null;
  categoria_id: number | null;
  temporada_id: number | null;
}

export interface PromocionAlcanceCrear {
  producto_id?: number | null;
  categoria_id?: number | null;
  temporada_id?: number | null;
}

export interface Promocion {
  id: number;
  nombre: string;
  tipo: TipoPromocion;
  valor: number;
  fecha_inicio: string;
  fecha_fin: string;
  activo: boolean;
  alcances: PromocionAlcance[];
}

export interface PromocionCrear {
  nombre: string;
  tipo: TipoPromocion;
  valor: number;
  fecha_inicio: string;
  fecha_fin: string;
  alcances: PromocionAlcanceCrear[];
}

export interface PromocionActualizar {
  nombre?: string;
  valor?: number;
  fecha_inicio?: string;
  fecha_fin?: string;
  activo?: boolean;
}
