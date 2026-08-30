class GeneracionEstado {
  const GeneracionEstado({
    required this.id,
    required this.estado,
    this.urlResultado,
    this.mensajeError,
    this.desdeCache = false,
  });

  factory GeneracionEstado.fromJson(Map<String, dynamic> json) => GeneracionEstado(
    id: json['id'] as int,
    estado: json['estado'] as String,
    urlResultado: json['url_resultado'] as String?,
    mensajeError: json['mensaje_error'] as String?,
    desdeCache: json['desde_cache'] as bool? ?? false,
  );

  final int id;
  final String estado; // en_proceso | completado | fallido
  final String? urlResultado;
  final String? mensajeError;
  final bool desdeCache;

  bool get enProceso => estado == 'en_proceso';
  bool get completado => estado == 'completado';
  bool get fallido => estado == 'fallido';
}
