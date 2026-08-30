import 'package:dio/dio.dart';
import '../models/disponibilidad_sucursal.dart';

class DisponibilidadRepository {
  DisponibilidadRepository(this._dio);

  final Dio _dio;

  /// Endpoint público: no requiere sesión de cliente.
  Future<List<DisponibilidadSucursal>> porVariante(int varianteId) async {
    final respuesta = await _dio.get<List<dynamic>>(
      '/inventario/disponibilidad',
      queryParameters: {'variante_id': varianteId},
    );
    return respuesta.data!.map((e) => DisponibilidadSucursal.fromJson(e as Map<String, dynamic>)).toList();
  }
}
