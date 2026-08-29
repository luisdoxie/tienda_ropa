export interface Permiso {
  id: number;
  codigo: string;
  modulo: string;
  descripcion: string | null;
}

export interface Rol {
  id: number;
  nombre: string;
  descripcion: string | null;
  activo: boolean;
  permisos: Permiso[];
}

export interface RolCrear {
  nombre: string;
  descripcion?: string | null;
}

export type RolActualizar = Partial<RolCrear>;

export interface Usuario {
  id: number;
  nombre: string;
  apellido: string;
  email: string;
  telefono: string | null;
  activo: boolean;
  roles: string[];
}

export interface UsuarioYo extends Usuario {
  permisos: string[];
}

export interface UsuarioCrear {
  nombre: string;
  apellido: string;
  email: string;
  telefono?: string | null;
  password: string;
}

export interface UsuarioActualizar {
  nombre?: string;
  apellido?: string;
  telefono?: string | null;
  activo?: boolean;
}

export interface TokenRespuesta {
  access_token: string;
  refresh_token: string;
  token_type: string;
}
