import 'package:dio/dio.dart';

import '../models/voz_resultado.dart';

class VozRepository {
  VozRepository(this._dio);

  final Dio _dio;

  Future<VozResultado> buscarPorVoz(String texto) async {
    final respuesta = await _dio.post<Map<String, dynamic>>('/ia/voz', data: {'texto': texto});
    return VozResultado.fromJson(respuesta.data!);
  }
}
