import 'package:dio/dio.dart';
import '../models/catalogo_detalle.dart';
import '../models/catalogo_item.dart';
import '../models/filtros_catalogo.dart';
import '../models/variante_lookup.dart';

class CatalogoRepository {
  CatalogoRepository(this._dio);

  final Dio _dio;

  Future<List<CatalogoItem>> listar({required int pagina, required int tamanio}) async {
    final respuesta = await _dio.get<List<dynamic>>(
      '/catalogo',
      queryParameters: {'pagina': pagina, 'tamanio': tamanio},
    );
    return respuesta.data!.map((e) => CatalogoItem.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<List<CatalogoItem>> buscar(FiltrosCatalogo filtros, {required int pagina, required int tamanio}) async {
    final respuesta = await _dio.get<List<dynamic>>(
      '/catalogo/buscar',
      queryParameters: {'pagina': pagina, 'tamanio': tamanio, ...filtros.aQueryParams()},
    );
    return respuesta.data!.map((e) => CatalogoItem.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<CatalogoDetalle> detalle(int productoId) async {
    final respuesta = await _dio.get<Map<String, dynamic>>('/catalogo/$productoId');
    return CatalogoDetalle.fromJson(respuesta.data!);
  }

  /// Resuelve nombre/foto/talla/color en lote para un conjunto de
  /// variantes -- lo usa el carrito de compra (features/compras), que del
  /// backend solo recibe variante_id/cantidad/precio.
  Future<List<VarianteLookupItem>> detallePorVariantes(List<int> varianteIds) async {
    if (varianteIds.isEmpty) return const [];
    final respuesta = await _dio.get<List<dynamic>>(
      '/catalogo/variantes/detalle',
      queryParameters: {'variante_ids': varianteIds.join(',')},
    );
    return respuesta.data!.map((e) => VarianteLookupItem.fromJson(e as Map<String, dynamic>)).toList();
  }
}
