import 'package:dio/dio.dart';
import '../models/horario_sucursal.dart';

class HorariosRepository {
  HorariosRepository(this._dio);

  final Dio _dio;

  Future<List<HorarioSucursal>> porSucursal(int sucursalId) async {
    final respuesta = await _dio.get<List<dynamic>>('/sucursales/$sucursalId/horarios');
    return respuesta.data!.map((e) => HorarioSucursal.fromJson(e as Map<String, dynamic>)).toList();
  }
}
