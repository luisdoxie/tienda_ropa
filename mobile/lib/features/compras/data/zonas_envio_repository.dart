import 'package:dio/dio.dart';
import '../models/zona_envio.dart';

class ZonasEnvioRepository {
  ZonasEnvioRepository(this._dio);

  final Dio _dio;

  Future<List<ZonaEnvio>> listar() async {
    final respuesta = await _dio.get<List<dynamic>>('/zonas-envio');
    return respuesta.data!.map((e) => ZonaEnvio.fromJson(e as Map<String, dynamic>)).toList();
  }
}
