export interface ZonaEnvio {
  id: number;
  ciudad_id: number;
  nombre: string;
  anillo_desde: number | null;
  anillo_hasta: number | null;
  tarifa_base: number;
  activo: boolean;
}

export interface ZonaEnvioCrear {
  ciudad_id: number;
  nombre: string;
  anillo_desde?: number | null;
  anillo_hasta?: number | null;
  tarifa_base: number;
}

export interface ZonaEnvioActualizar {
  nombre?: string;
  anillo_desde?: number | null;
  anillo_hasta?: number | null;
  tarifa_base?: number;
  activo?: boolean;
}
