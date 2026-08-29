import 'package:dio/dio.dart';
import '../models/referencia.dart';

/// Catálogos de referencia (categoría, talla, color, material, temporada,
/// sucursal): son chicos, así que se pide una sola página grande en vez
/// de paginar.
class ReferenciaRepository {
  ReferenciaRepository(this._dio);

  final Dio _dio;

  static const _tamanioMaximo = 100;

  Future<List<CategoriaRef>> categorias() async {
    final r = await _dio.get<List<dynamic>>('/categorias', queryParameters: {'tamanio': _tamanioMaximo});
    return r.data!.map((e) => CategoriaRef.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<List<TallaRef>> tallas() async {
    final r = await _dio.get<List<dynamic>>('/tallas', queryParameters: {'tamanio': _tamanioMaximo});
    return r.data!.map((e) => TallaRef.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<List<ColorRef>> colores() async {
    final r = await _dio.get<List<dynamic>>('/colores', queryParameters: {'tamanio': _tamanioMaximo});
    return r.data!.map((e) => ColorRef.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<List<MaterialRef>> materiales() async {
    final r = await _dio.get<List<dynamic>>('/materiales', queryParameters: {'tamanio': _tamanioMaximo});
    return r.data!.map((e) => MaterialRef.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<List<TemporadaRef>> temporadas() async {
    final r = await _dio.get<List<dynamic>>('/temporadas', queryParameters: {'tamanio': _tamanioMaximo});
    return r.data!.map((e) => TemporadaRef.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<List<SucursalRef>> sucursales() async {
    final r = await _dio.get<List<dynamic>>('/sucursales', queryParameters: {'tamanio': _tamanioMaximo});
    return r.data!.map((e) => SucursalRef.fromJson(e as Map<String, dynamic>)).toList();
  }
}
