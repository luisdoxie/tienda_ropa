class FiltrosCatalogo {
  const FiltrosCatalogo({
    this.texto,
    this.categoriaId,
    this.tallaId,
    this.colorId,
    this.materialId,
    this.temporadaId,
    this.genero,
    this.precioMin,
    this.precioMax,
  });

  final String? texto;
  final int? categoriaId;
  final int? tallaId;
  final int? colorId;
  final int? materialId;
  final int? temporadaId;
  final String? genero;
  final double? precioMin;
  final double? precioMax;

  bool get tieneFiltros =>
      (texto != null && texto!.isNotEmpty) ||
      categoriaId != null ||
      tallaId != null ||
      colorId != null ||
      materialId != null ||
      temporadaId != null ||
      genero != null ||
      precioMin != null ||
      precioMax != null;

  Map<String, dynamic> aQueryParams() {
    return {
      if (texto != null && texto!.isNotEmpty) 'q': texto,
      if (categoriaId != null) 'categoria_id': categoriaId,
      if (tallaId != null) 'talla_id': tallaId,
      if (colorId != null) 'color_id': colorId,
      if (materialId != null) 'material_id': materialId,
      if (temporadaId != null) 'temporada_id': temporadaId,
      if (genero != null) 'genero': genero,
      if (precioMin != null) 'precio_min': precioMin,
      if (precioMax != null) 'precio_max': precioMax,
    };
  }

  FiltrosCatalogo copyWith({
    String? texto,
    int? categoriaId,
    int? tallaId,
    int? colorId,
    int? materialId,
    int? temporadaId,
    String? genero,
    double? precioMin,
    double? precioMax,
    bool limpiarTexto = false,
    bool limpiarCategoria = false,
    bool limpiarTalla = false,
    bool limpiarColor = false,
    bool limpiarMaterial = false,
    bool limpiarTemporada = false,
    bool limpiarGenero = false,
    bool limpiarPrecioMin = false,
    bool limpiarPrecioMax = false,
  }) {
    return FiltrosCatalogo(
      texto: limpiarTexto ? null : (texto ?? this.texto),
      categoriaId: limpiarCategoria ? null : (categoriaId ?? this.categoriaId),
      tallaId: limpiarTalla ? null : (tallaId ?? this.tallaId),
      colorId: limpiarColor ? null : (colorId ?? this.colorId),
      materialId: limpiarMaterial ? null : (materialId ?? this.materialId),
      temporadaId: limpiarTemporada ? null : (temporadaId ?? this.temporadaId),
      genero: limpiarGenero ? null : (genero ?? this.genero),
      precioMin: limpiarPrecioMin ? null : (precioMin ?? this.precioMin),
      precioMax: limpiarPrecioMax ? null : (precioMax ?? this.precioMax),
    );
  }
}
