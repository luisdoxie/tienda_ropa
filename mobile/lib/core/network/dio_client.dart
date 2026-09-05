import 'package:dio/dio.dart';
import '../config/api_config.dart';
import 'token_storage.dart';

const _rutasPublicas = ['/auth/login', '/auth/registro', '/auth/refresh', '/auth/recuperar', '/catalogo'];

bool _esRutaPublica(String path) => _rutasPublicas.any((ruta) => path.contains(ruta));

/// Cliente Dio con JWT automático y refresh transparente en 401.
///
/// [onSesionExpirada] se llama cuando el refresh también falla (el refresh
/// token venció o es inválido): ahí es responsabilidad de quien arma el
/// cliente cerrar la sesión de verdad (limpiar estado, redirigir a login).
///
/// Dos cosas evitan el bucle infinito si el refresh token también expiró:
/// 1. Cada request reintentada se marca con `extra['reintentado'] = true`;
///    si vuelve a dar 401, no se reintenta una segunda vez, se propaga el
///    error tal cual.
/// 2. Si ya hay un refresh en curso, las demás requests que reciben 401 al
///    mismo tiempo esperan ese mismo refresh en vez de disparar uno cada una.
Dio buildDio({
  required TokenStorage tokenStorage,
  required Future<void> Function() onSesionExpirada,
}) {
  final dio = Dio(
    BaseOptions(
      baseUrl: ApiConfig.baseUrl,
      connectTimeout: const Duration(seconds: 15),
      receiveTimeout: const Duration(seconds: 15),
    ),
  );

  // Dio aparte, sin interceptores, para llamar a /auth/refresh sin
  // reentrar en este mismo flujo de manejo de 401.
  final dioRefresh = Dio(BaseOptions(baseUrl: ApiConfig.baseUrl));

  Future<String>? refrescoEnCurso;

  Future<String> refrescarToken() async {
    final refreshToken = await tokenStorage.leerRefreshToken();
    if (refreshToken == null) {
      throw DioException(
        requestOptions: RequestOptions(path: '/auth/refresh'),
        error: 'No hay refresh token guardado',
      );
    }

    // dioRefresh siempre habla por el mismo transporte que dio (relevante
    // sobre todo en tests, que reemplazan el adapter después de armar el
    // cliente).
    dioRefresh.httpClientAdapter = dio.httpClientAdapter;
    final respuesta = await dioRefresh.post<Map<String, dynamic>>(
      '/auth/refresh',
      data: {'refresh_token': refreshToken},
    );

    final datos = respuesta.data!;
    final nuevoAccessToken = datos['access_token'] as String;
    final nuevoRefreshToken = datos['refresh_token'] as String;
    await tokenStorage.guardar(accessToken: nuevoAccessToken, refreshToken: nuevoRefreshToken);
    return nuevoAccessToken;
  }

  dio.interceptors.add(
    InterceptorsWrapper(
      onRequest: (options, handler) async {
        if (!_esRutaPublica(options.path)) {
          final token = await tokenStorage.leerAccessToken();
          if (token != null) {
            options.headers['Authorization'] = 'Bearer $token';
          }
        }
        handler.next(options);
      },
      onError: (error, handler) async {
        final esNoAutorizado = error.response?.statusCode == 401;
        final yaReintentado = error.requestOptions.extra['reintentado'] == true;

        if (!esNoAutorizado || _esRutaPublica(error.requestOptions.path) || yaReintentado) {
          handler.next(error);
          return;
        }

        try {
          refrescoEnCurso ??= refrescarToken();
          final nuevoAccessToken = await refrescoEnCurso;
          refrescoEnCurso = null;

          final opciones = error.requestOptions;
          opciones.extra = {...opciones.extra, 'reintentado': true};
          opciones.headers['Authorization'] = 'Bearer $nuevoAccessToken';

          final respuesta = await dio.fetch(opciones);
          handler.resolve(respuesta);
        } catch (_) {
          refrescoEnCurso = null;
          await tokenStorage.limpiar();
          await onSesionExpirada();
          handler.next(error);
        }
      },
    ),
  );

  return dio;
}
