import 'package:dio/dio.dart';
import '../models/notificacion_app.dart';

class NotificacionesRepository {
  NotificacionesRepository(this._dio);

  final Dio _dio;

  Future<List<NotificacionApp>> listar() async {
    final respuesta = await _dio.get<List<dynamic>>('/notificaciones');
    return respuesta.data!.map((e) => NotificacionApp.fromJson(e as Map<String, dynamic>)).toList();
  }
}
