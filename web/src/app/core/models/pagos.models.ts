export type MetodoPagoCaja = 'efectivo' | 'qr' | 'tarjeta' | 'transferencia';
export type EstadoPago = 'iniciado' | 'aprobado' | 'rechazado' | 'reembolsado';

export interface PagoCajaRequest {
  venta_id: number;
  metodo_pago: MetodoPagoCaja;
  monto_recibido?: number | null;
}

export interface Pago {
  id: number;
  venta_id: number;
  monto: number;
  referencia_externa: string | null;
  fecha: string;
  metodo_pago: string;
  estado: EstadoPago;
}

export interface PagoCajaRespuesta {
  pago: Pago;
  cambio: number | null;
}
