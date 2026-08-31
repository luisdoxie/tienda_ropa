export interface VarianteBusqueda {
  variante_id: number;
  producto_id: number;
  producto_nombre: string;
  producto_codigo: string;
  talla_codigo: string;
  color_nombre: string;
  sku: string;
  codigo_barras: string | null;
  precio_efectivo: number;
}
