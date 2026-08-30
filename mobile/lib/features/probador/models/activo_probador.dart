class Ancla {
  const Ancla({required this.x, required this.y});

  factory Ancla.fromJson(Map<String, dynamic> json) =>
      Ancla(x: (json['x'] as num).toDouble(), y: (json['y'] as num).toDouble());

  final double x;
  final double y;
}

class AnclajesProbador {
  const AnclajesProbador({required this.hombroIzq, required this.hombroDer, required this.cadera});

  factory AnclajesProbador.fromJson(Map<String, dynamic> json) => AnclajesProbador(
    hombroIzq: Ancla.fromJson(json['hombro_izq'] as Map<String, dynamic>),
    hombroDer: Ancla.fromJson(json['hombro_der'] as Map<String, dynamic>),
    cadera: Ancla.fromJson(json['cadera'] as Map<String, dynamic>),
  );

  final Ancla hombroIzq;
  final Ancla hombroDer;
  final Ancla cadera;
}

class ActivoProbador {
  const ActivoProbador({
    required this.id,
    required this.varianteId,
    required this.tipo,
    required this.publicId,
    required this.url,
    required this.anclajes,
    required this.anchoPx,
    required this.altoPx,
    required this.estado,
  });

  factory ActivoProbador.fromJson(Map<String, dynamic> json) => ActivoProbador(
    id: json['id'] as int,
    varianteId: json['variante_id'] as int,
    tipo: json['tipo'] as String,
    publicId: json['public_id'] as String,
    url: json['url'] as String,
    anclajes: json['anclajes'] == null
        ? null
        : AnclajesProbador.fromJson(json['anclajes'] as Map<String, dynamic>),
    anchoPx: json['ancho_px'] as int?,
    altoPx: json['alto_px'] as int?,
    estado: json['estado'] as String,
  );

  final int id;
  final int varianteId;
  final String tipo;
  final String publicId;
  final String url;
  final AnclajesProbador? anclajes;
  final int? anchoPx;
  final int? altoPx;
  final String estado;
}

class AssetsVariante {
  const AssetsVariante({required this.overlay, required this.flatlay});

  factory AssetsVariante.fromJson(Map<String, dynamic> json) => AssetsVariante(
    overlay: ActivoProbador.fromJson(json['overlay'] as Map<String, dynamic>),
    flatlay: json['flatlay'] == null ? null : ActivoProbador.fromJson(json['flatlay'] as Map<String, dynamic>),
  );

  final ActivoProbador overlay;
  final ActivoProbador? flatlay;
}
