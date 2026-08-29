class CatalogoItem {
  const CatalogoItem({
    required this.id,
    required this.codigo,
    required this.nombre,
    required this.categoriaId,
    required this.genero,
    required this.precioBase,
    required this.admiteProbador,
    required this.imagenPrincipal,
  });

  factory CatalogoItem.fromJson(Map<String, dynamic> json) {
    return CatalogoItem(
      id: json['id'] as int,
      codigo: json['codigo'] as String,
      nombre: json['nombre'] as String,
      categoriaId: json['categoria_id'] as int,
      genero: json['genero'] as String,
      precioBase: double.parse(json['precio_base'].toString()),
      admiteProbador: json['admite_probador'] as bool,
      imagenPrincipal: json['imagen_principal'] as String?,
    );
  }

  final int id;
  final String codigo;
  final String nombre;
  final int categoriaId;
  final String genero;
  final double precioBase;
  final bool admiteProbador;
  final String? imagenPrincipal;
}
