import '../../catalogo/models/catalogo_item.dart';
import '../../catalogo/models/filtros_catalogo.dart';

/// Respuesta de POST /ia/voz: trae los resultados YA buscados (para no
/// pegarle una segunda vez a /catalogo/buscar), los filtros que se
/// aplicaron (mismo shape que FiltrosCatalogo, reusable tal cual en
/// CatalogoController) y una etiqueta legible por cada filtro activo, para
/// mostrar como chip.
class VozResultado {
  const VozResultado({
    required this.resultados,
    required this.filtros,
    required this.etiquetas,
    required this.cantidad,
  });

  factory VozResultado.fromJson(Map<String, dynamic> json) {
    return VozResultado(
      resultados: (json['resultados'] as List<dynamic>)
          .map((e) => CatalogoItem.fromJson(e as Map<String, dynamic>))
          .toList(),
      filtros: _filtrosDesdeJson(json['filtros'] as Map<String, dynamic>),
      etiquetas: (json['etiquetas'] as Map<String, dynamic>).map((clave, valor) => MapEntry(clave, valor as String)),
      cantidad: json['cantidad'] as int,
    );
  }

  final List<CatalogoItem> resultados;
  final FiltrosCatalogo filtros;
  final Map<String, String> etiquetas;
  final int cantidad;
}

FiltrosCatalogo _filtrosDesdeJson(Map<String, dynamic> json) {
  return FiltrosCatalogo(
    texto: json['texto'] as String?,
    categoriaId: json['categoria_id'] as int?,
    tallaId: json['talla_id'] as int?,
    colorId: json['color_id'] as int?,
    materialId: json['material_id'] as int?,
    temporadaId: json['temporada_id'] as int?,
    genero: json['genero'] as String?,
    precioMin: json['precio_min'] == null ? null : double.parse(json['precio_min'].toString()),
    precioMax: json['precio_max'] == null ? null : double.parse(json['precio_max'].toString()),
  );
}
