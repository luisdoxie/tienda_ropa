import 'package:dio/dio.dart';
import '../models/favorito.dart';

class FavoritosRepository {
  FavoritosRepository(this._dio);

  final Dio _dio;

  Future<List<Favorito>> listar() async {
    final r = await _dio.get<List<dynamic>>('/favoritos');
    return r.data!.map((e) => Favorito.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<void> agregar(int varianteId) => _dio.post<void>('/favoritos', data: {'variante_id': varianteId});

  Future<void> quitar(int varianteId) => _dio.delete<void>('/favoritos/$varianteId');
}
