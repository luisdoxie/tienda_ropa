import 'package:dio/dio.dart';
import '../models/reserva.dart';

class ReservasRepository {
  ReservasRepository(this._dio);

  final Dio _dio;

  Future<Reserva> crear({
    required int sucursalId,
    required String fechaVisita,
    required String horaVisitaDesde,
    required String horaVisitaHasta,
    required List<int> variantesIds,
  }) async {
    final respuesta = await _dio.post<Map<String, dynamic>>(
      '/reservas',
      data: {
        'sucursal_id': sucursalId,
        'fecha_visita': fechaVisita,
        'hora_visita_desde': horaVisitaDesde,
        'hora_visita_hasta': horaVisitaHasta,
        'detalle': variantesIds.map((id) => {'variante_id': id, 'cantidad': 1}).toList(),
      },
    );
    return Reserva.fromJson(respuesta.data!);
  }

  Future<List<Reserva>> misReservas() async {
    final respuesta = await _dio.get<List<dynamic>>('/reservas/mis-reservas');
    return respuesta.data!.map((e) => Reserva.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<Reserva> obtener(int id) async {
    final respuesta = await _dio.get<Map<String, dynamic>>('/reservas/$id');
    return Reserva.fromJson(respuesta.data!);
  }

  Future<Reserva> cancelar(int id) async {
    final respuesta = await _dio.delete<Map<String, dynamic>>('/reservas/$id');
    return Reserva.fromJson(respuesta.data!);
  }
}
