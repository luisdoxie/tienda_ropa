import 'package:dio/dio.dart';
import '../models/carrito.dart';

class CarritoRepository {
  CarritoRepository(this._dio);

  final Dio _dio;

  Future<Carrito> obtener() async {
    final respuesta = await _dio.get<Map<String, dynamic>>('/carrito');
    return Carrito.fromJson(respuesta.data!);
  }

  Future<Carrito> agregar({required int varianteId, required int cantidad}) async {
    final respuesta = await _dio.post<Map<String, dynamic>>(
      '/carrito',
      data: {'variante_id': varianteId, 'cantidad': cantidad},
    );
    return Carrito.fromJson(respuesta.data!);
  }

  Future<Carrito> actualizarCantidad({required int varianteId, required int cantidad}) async {
    final respuesta = await _dio.put<Map<String, dynamic>>('/carrito/$varianteId', data: {'cantidad': cantidad});
    return Carrito.fromJson(respuesta.data!);
  }

  Future<Carrito> quitar(int varianteId) async {
    final respuesta = await _dio.delete<Map<String, dynamic>>('/carrito/$varianteId');
    return Carrito.fromJson(respuesta.data!);
  }

  Future<ResumenCarrito> aplicarPromocion() async {
    final respuesta = await _dio.post<Map<String, dynamic>>('/carrito/aplicar-promocion');
    return ResumenCarrito.fromJson(respuesta.data!);
  }
}
