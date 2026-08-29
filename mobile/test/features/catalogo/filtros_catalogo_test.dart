import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/features/catalogo/models/filtros_catalogo.dart';

void main() {
  group('FiltrosCatalogo', () {
    test('sin filtros, tieneFiltros es false y no genera query params', () {
      const filtros = FiltrosCatalogo();
      expect(filtros.tieneFiltros, isFalse);
      expect(filtros.aQueryParams(), isEmpty);
    });

    test('con al menos un filtro, tieneFiltros es true', () {
      const filtros = FiltrosCatalogo(categoriaId: 3);
      expect(filtros.tieneFiltros, isTrue);
      expect(filtros.aQueryParams(), {'categoria_id': 3});
    });

    test('texto vacío no cuenta como filtro activo', () {
      const filtros = FiltrosCatalogo(texto: '');
      expect(filtros.tieneFiltros, isFalse);
      expect(filtros.aQueryParams(), isEmpty);
    });

    test('aQueryParams incluye todos los filtros seteados', () {
      const filtros = FiltrosCatalogo(
        texto: 'camisa',
        categoriaId: 1,
        tallaId: 2,
        colorId: 3,
        materialId: 4,
        temporadaId: 5,
        genero: 'hombre',
        precioMin: 50,
        precioMax: 200,
      );
      expect(filtros.aQueryParams(), {
        'q': 'camisa',
        'categoria_id': 1,
        'talla_id': 2,
        'color_id': 3,
        'material_id': 4,
        'temporada_id': 5,
        'genero': 'hombre',
        'precio_min': 50.0,
        'precio_max': 200.0,
      });
    });

    test('copyWith con limpiar* borra el filtro en vez de conservarlo', () {
      const filtros = FiltrosCatalogo(categoriaId: 3, genero: 'mujer');
      final resultado = filtros.copyWith(limpiarCategoria: true);

      expect(resultado.categoriaId, isNull);
      expect(resultado.genero, 'mujer'); // el resto no se toca
    });
  });
}
