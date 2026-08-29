export interface Ciudad {
  id: number;
  nombre: string;
  departamento: string | null;
  activo: boolean;
}

export interface CiudadCrear {
  nombre: string;
  departamento?: string | null;
}

export type CiudadActualizar = Partial<CiudadCrear>;

export interface Sucursal {
  id: number;
  ciudad_id: number;
  codigo: string;
  nombre: string;
  direccion: string;
  telefono: string | null;
  latitud: number | null;
  longitud: number | null;
  es_deposito: boolean;
  activo: boolean;
  creado_en: string;
}

export interface SucursalCrear {
  ciudad_id: number;
  codigo: string;
  nombre: string;
  direccion: string;
  telefono?: string | null;
  es_deposito?: boolean;
}

export type SucursalActualizar = Partial<SucursalCrear> & { activo?: boolean };
