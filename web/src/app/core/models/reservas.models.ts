export type EstadoReserva = 'pendiente' | 'preparada' | 'en_prueba' | 'completada' | 'cancelada' | 'expirada';

export interface ReservaDetalle {
  id: number;
  variante_id: number;
  cantidad: number;
  seleccionada: boolean | null;
  preparada: boolean;
}

export interface ReservaHistorialItem {
  id: number;
  estado: EstadoReserva;
  usuario_id: number | null;
  comentario: string | null;
  creado_en: string;
}

export interface Reserva {
  id: number;
  codigo: string;
  cliente_id: number;
  sucursal_id: number;
  estado: EstadoReserva;
  fecha_visita: string;
  hora_visita_desde: string;
  hora_visita_hasta: string;
  fecha_expiracion: string;
  observacion: string | null;
  creado_en: string;
  detalle: ReservaDetalle[];
  historial: ReservaHistorialItem[];
}

export interface SeleccionLinea {
  variante_id: number;
  seleccionada: boolean;
}

export interface SeleccionActualizar {
  lineas: SeleccionLinea[];
}
