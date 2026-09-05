import 'package:dio/dio.dart';
import '../models/cotizacion_envio.dart';
import '../models/envio.dart';

class EnviosRepository {
  EnviosRepository(this._dio);

  final Dio _dio;

  Future<CotizacionEnvio> cotizar({required int direccionId, required int cantidadPrendas}) async {
    final respuesta = await _dio.post<Map<String, dynamic>>(
      '/envios/cotizar',
      data: {'direccion_id': direccionId, 'cantidad_prendas': cantidadPrendas},
    );
    return CotizacionEnvio.fromJson(respuesta.data!);
  }

  Future<Envio> crear({required int ventaId, required int direccionId}) async {
    final respuesta = await _dio.post<Map<String, dynamic>>(
      '/envios',
      data: {'venta_id': ventaId, 'direccion_id': direccionId},
    );
    return Envio.fromJson(respuesta.data!);
  }
}
