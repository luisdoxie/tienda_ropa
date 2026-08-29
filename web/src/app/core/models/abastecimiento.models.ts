export interface Proveedor {
  id: number;
  nombre: string;
  nit: string | null;
  contacto: string | null;
  telefono: string | null;
  email: string | null;
  direccion: string | null;
  usuario_id: number | null;
  activo: boolean;
  creado_en: string;
}

export interface RecepcionDetalleCrear {
  variante_id: number;
  cantidad: number;
  costo_unitario: number;
}

export interface RecepcionCrear {
  codigo: string;
  orden_compra_id?: number | null;
  proveedor_id: number;
  sucursal_id: number;
  observacion?: string | null;
  detalle: RecepcionDetalleCrear[];
}

export interface RecepcionDetalle {
  id: number;
  variante_id: number;
  cantidad: number;
  costo_unitario: number;
}

export interface Recepcion {
  id: number;
  codigo: string;
  orden_compra_id: number | null;
  proveedor_id: number;
  sucursal_id: number;
  empleado_id: number | null;
  fecha: string;
  observacion: string | null;
  detalle: RecepcionDetalle[];
}
