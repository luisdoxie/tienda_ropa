import 'package:dio/dio.dart';
import '../models/direccion_cliente.dart';

class DireccionesRepository {
  DireccionesRepository(this._dio);

  final Dio _dio;

  Future<List<DireccionCliente>> misDirecciones() async {
    final respuesta = await _dio.get<List<dynamic>>('/clientes/direcciones');
    return respuesta.data!.map((e) => DireccionCliente.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<DireccionCliente> crear({
    required int? zonaEnvioId,
    required String? alias,
    required String direccion,
    required String? referencia,
    required bool esPrincipal,
  }) async {
    final respuesta = await _dio.post<Map<String, dynamic>>(
      '/clientes/direcciones',
      data: {
        'zona_envio_id': zonaEnvioId,
        'alias': alias,
        'direccion': direccion,
        'referencia': referencia,
        'es_principal': esPrincipal,
      },
    );
    return DireccionCliente.fromJson(respuesta.data!);
  }
}
