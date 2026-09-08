import '../../catalogo/models/catalogo_item.dart';

/// Una recomendación del carrusel (P6.2): la tarjeta de producto (mismo
/// modelo que usa el grid del catálogo) + el motivo en lenguaje natural
/// que arma el backend.
class RecomendacionItem {
  const RecomendacionItem({required this.varianteId, required this.producto, required this.motivo});

  factory RecomendacionItem.fromJson(Map<String, dynamic> json) {
    return RecomendacionItem(
      varianteId: json['variante_id'] as int,
      producto: CatalogoItem.fromJson(json['producto'] as Map<String, dynamic>),
      motivo: json['motivo'] as String,
    );
  }

  final int varianteId;
  final CatalogoItem producto;
  final String motivo;
}
