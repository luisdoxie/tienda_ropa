/// Una línea de la lista temporal que arma el cliente desde el detalle de
/// producto, antes de confirmar la reserva. Vive solo en memoria (ver
/// CarritoReservaController): si se cierra la app, se pierde.
class ItemReservaTemporal {
  const ItemReservaTemporal({
    required this.varianteId,
    required this.productoNombre,
    required this.sku,
    required this.tallaCodigo,
    required this.colorNombre,
    this.imagenUrl,
  });

  final int varianteId;
  final String productoNombre;
  final String sku;
  final String tallaCodigo;
  final String colorNombre;
  final String? imagenUrl;
}
