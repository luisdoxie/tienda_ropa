import 'dart:async';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/core/network/dio_client.dart';

import '../../helpers/token_storage_falso.dart';

/// Adaptador HTTP falso: simula el backend sin hacer red real.
class AdaptadorFalso implements HttpClientAdapter {
  AdaptadorFalso(this.responder);

  final Future<ResponseBody> Function(RequestOptions options) responder;

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) {
    return responder(options);
  }

  @override
  void close({bool force = false}) {}
}

ResponseBody _json(String cuerpo, int status) {
  return ResponseBody.fromString(
    cuerpo,
    status,
    headers: {
      Headers.contentTypeHeader: [Headers.jsonContentType],
    },
  );
}

void main() {
  group('buildDio - refresh automático', () {
    test('un 401 dispara refresh y reintenta la request original una sola vez', () async {
      final storage = TokenStorageFalso()
        ..accessToken = 'ACCESS_VIEJO'
        ..refreshToken = 'REFRESH_VALIDO';
      var sesionesExpiradas = 0;
      var llamadasRefresh = 0;

      final dio = buildDio(
        tokenStorage: storage,
        onSesionExpirada: () async => sesionesExpiradas++,
      );

      dio.httpClientAdapter = AdaptadorFalso((options) async {
        if (options.path.contains('/auth/refresh')) {
          llamadasRefresh++;
          return _json('{"access_token":"ACCESS_NUEVO","refresh_token":"REFRESH_NUEVO"}', 200);
        }

        final auth = options.headers['Authorization'];
        if (auth == 'Bearer ACCESS_NUEVO') {
          return _json('{"ok":true}', 200);
        }
        return _json('{"detail":"Token inválido o expirado"}', 401);
      });

      final respuesta = await dio.get<Map<String, dynamic>>('/protegido');

      expect(respuesta.statusCode, 200);
      expect(llamadasRefresh, 1);
      expect(sesionesExpiradas, 0);
      expect(storage.accessToken, 'ACCESS_NUEVO');
    });

    test('si el refresh token también venció, no reintenta en bucle: falla una vez y cierra sesión', () async {
      final storage = TokenStorageFalso()
        ..accessToken = 'ACCESS_VIEJO'
        ..refreshToken = 'REFRESH_VENCIDO';
      var sesionesExpiradas = 0;
      var llamadasRefresh = 0;
      var llamadasProtegido = 0;

      final dio = buildDio(
        tokenStorage: storage,
        onSesionExpirada: () async => sesionesExpiradas++,
      );

      dio.httpClientAdapter = AdaptadorFalso((options) async {
        if (options.path.contains('/auth/refresh')) {
          llamadasRefresh++;
          return _json('{"detail":"Token inválido o expirado"}', 401);
        }
        llamadasProtegido++;
        return _json('{"detail":"Token inválido o expirado"}', 401);
      });

      await expectLater(dio.get<Map<String, dynamic>>('/protegido'), throwsA(isA<DioException>()));

      // Ni el refresh ni la request protegida se reintentan más de una vez:
      // esto es lo que evita el bucle infinito si el refresh token expiró.
      expect(llamadasRefresh, 1);
      expect(llamadasProtegido, 1);
      expect(sesionesExpiradas, 1);
      expect(storage.accessToken, isNull);
      expect(storage.refreshToken, isNull);
      expect(storage.vecesLimpiado, 1);
    });

    test('dos 401 concurrentes comparten un único refresh en curso', () async {
      final storage = TokenStorageFalso()
        ..accessToken = 'ACCESS_VIEJO'
        ..refreshToken = 'REFRESH_VALIDO';
      var llamadasRefresh = 0;
      final refreshCompleter = Completer<void>();

      final dio = buildDio(tokenStorage: storage, onSesionExpirada: () async {});

      dio.httpClientAdapter = AdaptadorFalso((options) async {
        if (options.path.contains('/auth/refresh')) {
          llamadasRefresh++;
          // Se demora a propósito para que las dos requests concurrentes
          // lleguen a pedir refresh antes de que el primero termine.
          await refreshCompleter.future;
          return _json('{"access_token":"ACCESS_NUEVO","refresh_token":"REFRESH_NUEVO"}', 200);
        }

        final auth = options.headers['Authorization'];
        if (auth == 'Bearer ACCESS_NUEVO') {
          return _json('{"ok":true}', 200);
        }
        return _json('{"detail":"vencido"}', 401);
      });

      final futuro1 = dio.get<Map<String, dynamic>>('/protegido');
      final futuro2 = dio.get<Map<String, dynamic>>('/protegido');

      // Deja que ambas requests entren al interceptor y pidan refresh.
      await Future<void>.delayed(const Duration(milliseconds: 50));
      refreshCompleter.complete();

      final resultados = await Future.wait([futuro1, futuro2]);

      expect(resultados[0].statusCode, 200);
      expect(resultados[1].statusCode, 200);
      expect(llamadasRefresh, 1);
    });
  });
}
