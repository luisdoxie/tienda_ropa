export interface Notificacion {
  id: number;
  titulo: string;
  mensaje: string | null;
  tipo: string | null;
  referencia_id: number | null;
  leida: boolean;
  creado_en: string;
}
