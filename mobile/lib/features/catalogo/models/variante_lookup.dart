/// Fila de GET /catalogo/variantes/detalle: resuelve nombre+foto+talla+color
/// en lote a partir de un variante_id. La usa el carrito de compra, que solo
/// conoce variante_id/cantidad/precio (ver CarritoLinea).
class VarianteLookupItem {
  const VarianteLookupItem({
    required this.varianteId,
    required this.productoId,
    required this.productoNombre,
    required this.imagenPrincipal,
    required this.tallaCodigo,
    required this.colorNombre,
  });

  factory VarianteLookupItem.fromJson(Map<String, dynamic> json) => VarianteLookupItem(
    varianteId: json['variante_id'] as int?,
    productoId: json['producto_id'] as int,
    productoNombre: json['producto_nombre'] as String,
    imagenPrincipal: json['imagen_principal'] as String?,
    tallaCodigo: json['talla_codigo'] as String?,
    colorNombre: json['color_nombre'] as String?,
  );

  final int? varianteId;
  final int productoId;
  final String productoNombre;
  final String? imagenPrincipal;
  final String? tallaCodigo;
  final String? colorNombre;
}
