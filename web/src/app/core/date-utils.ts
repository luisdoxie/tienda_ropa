/** `venta.fecha`/`reserva.fecha_visita` vienen del backend en hora LOCAL
 * del servidor, sin offset (server_default now() de Postgres) -- comparar
 * contra toISOString() (UTC) desalinea la fecha cerca de medianoche. Se
 * arma "hoy" con el mismo calendario local, no UTC. */
export function fechaLocalIso(fecha: Date): string {
  const y = fecha.getFullYear();
  const m = String(fecha.getMonth() + 1).padStart(2, '0');
  const d = String(fecha.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}
