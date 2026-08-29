enum TipoEvento { vista, busqueda, favorito }

/// Modelo del evento que va a POST /api/v1/ia/eventos (todavía no existe:
/// llega en la etapa 6, paquete `inteligencia`, y alimenta el
/// recomendador). Se define ahora para que el registro funcione desde el
/// primer día, como pide el enunciado.
class Evento {
  const Evento({required this.tipo, this.productoId, this.varianteId, this.texto, required this.creadoEn});

  final TipoEvento tipo;
  final int? productoId;
  final int? varianteId;
  final String? texto;
  final DateTime creadoEn;

  Map<String, dynamic> toJson() {
    return {
      'tipo': tipo.name,
      if (productoId != null) 'producto_id': productoId,
      if (varianteId != null) 'variante_id': varianteId,
      if (texto != null) 'texto': texto,
      'creado_en': creadoEn.toIso8601String(),
    };
  }
}
