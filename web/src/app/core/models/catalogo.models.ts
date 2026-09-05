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

/** Fila de GET /catalogo/variantes/detalle -- ver dashboard.component.ts. */
export interface ProductoImagenLookupItem {
  variante_id: number | null;
  producto_id: number;
  producto_nombre: string;
  imagen_principal: string | null;
  talla_codigo: string | null;
  color_nombre: string | null;
}

export interface Categoria {
  id: number;
  categoria_padre_id: number | null;
  nombre: string;
  descripcion: string | null;
  activo: boolean;
}

export interface CategoriaCrear {
  nombre: string;
  descripcion?: string | null;
  categoria_padre_id?: number | null;
}

export type CategoriaActualizar = Partial<CategoriaCrear>;

export interface Material {
  id: number;
  nombre: string;
  descripcion: string | null;
}

export interface Temporada {
  id: number;
  nombre: string;
  anio: number;
  fecha_inicio: string | null;
  fecha_fin: string | null;
  activo: boolean;
}

export interface TemporadaCrear {
  nombre: string;
  anio: number;
  fecha_inicio?: string | null;
  fecha_fin?: string | null;
}

export interface TemporadaActualizar extends Partial<TemporadaCrear> {
  activo?: boolean;
}

export interface Coleccion {
  id: number;
  temporada_id: number | null;
  nombre: string;
  descripcion: string | null;
  activo: boolean;
}

export interface ColeccionCrear {
  temporada_id?: number | null;
  nombre: string;
  descripcion?: string | null;
}

export interface ColeccionActualizar extends Partial<ColeccionCrear> {
  activo?: boolean;
}

export type Genero = 'hombre' | 'mujer' | 'unisex' | 'nino';

/** Fila de GET /catalogo y /catalogo/buscar -- catálogo público, sin login. */
export interface CatalogoItem {
  id: number;
  codigo: string;
  nombre: string;
  categoria_id: number;
  genero: Genero;
  precio_base: number;
  admite_probador: boolean;
  imagen_principal: string | null;
}

export interface Talla {
  id: number;
  codigo: string;
  descripcion: string | null;
  orden: number;
}

export interface TallaCrear {
  codigo: string;
  descripcion?: string | null;
  orden?: number;
}

export type TallaActualizar = Partial<TallaCrear>;

export interface Color {
  id: number;
  nombre: string;
  codigo_hex: string | null;
}

export interface ColorCrear {
  nombre: string;
  codigo_hex?: string | null;
}

export type ColorActualizar = Partial<ColorCrear>;

export interface VarianteCatalogo {
  id: number;
  talla_id: number;
  color_id: number;
  sku: string;
  precio_efectivo: number;
  cantidad_disponible: number | null;
}

export interface ImagenProducto {
  id: number;
  producto_id: number;
  color_id: number | null;
  public_id: string;
  url: string;
  orden: number;
  es_principal: boolean;
}

/** Fila de GET /catalogo/{id} -- detalle público de un producto. */
export interface CatalogoDetalle {
  id: number;
  codigo: string;
  nombre: string;
  descripcion: string | null;
  categoria_id: number;
  genero: Genero;
  precio_base: number;
  admite_probador: boolean;
  variantes: VarianteCatalogo[];
  imagenes: ImagenProducto[];
}

// ---- Administración de productos (back office) ------------------------------

export interface Producto {
  id: number;
  codigo: string;
  nombre: string;
  descripcion: string | null;
  categoria_id: number;
  material_id: number | null;
  temporada_id: number | null;
  coleccion_id: number | null;
  genero: Genero;
  precio_base: number;
  admite_probador: boolean;
  activo: boolean;
  creado_en: string;
  creado_por: number | null;
}

export interface ProductoCrear {
  codigo: string;
  nombre: string;
  descripcion?: string | null;
  categoria_id: number;
  material_id?: number | null;
  temporada_id?: number | null;
  coleccion_id?: number | null;
  genero: Genero;
  precio_base: number;
  admite_probador?: boolean;
  tallas_ids: number[];
  colores_ids: number[];
}

export interface ProductoActualizar {
  codigo?: string;
  nombre?: string;
  descripcion?: string | null;
  categoria_id?: number;
  material_id?: number | null;
  temporada_id?: number | null;
  coleccion_id?: number | null;
  genero?: Genero;
  precio_base?: number;
  admite_probador?: boolean;
  activo?: boolean;
}

/** Variante vista desde la administración (a diferencia de `VarianteCatalogo`,
 * que es la vista pública dentro de CatalogoDetalle). */
export interface VarianteAdmin {
  id: number;
  producto_id: number;
  talla_id: number;
  color_id: number;
  sku: string;
  codigo_barras: string | null;
  precio: number | null;
  precio_efectivo: number;
  activo: boolean;
}

export interface VarianteActualizar {
  precio?: number | null;
  codigo_barras?: string | null;
  activo?: boolean;
}

export interface VariantesGenerarRequest {
  tallas_ids: number[];
  colores_ids: number[];
}
