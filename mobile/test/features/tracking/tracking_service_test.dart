import 'dart:async';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/features/tracking/models/evento.dart';
import 'package:mobile/features/tracking/state/tracking_service.dart';

class _AdaptadorFalso implements HttpClientAdapter {
  _AdaptadorFalso(this.responder);

  final Future<ResponseBody> Function(RequestOptions options) responder;

  @override
  Future<ResponseBody> fetch(RequestOptions options, Stream<Uint8List>? requestStream, Future<void>? cancelFuture) {
    return responder(options);
  }

  @override
  void close({bool force = false}) {}
}

ResponseBody _json(String cuerpo, int status) {
  return ResponseBody.fromString(cuerpo, status, headers: {'content-type': ['application/json']});
}

void main() {
  group('TrackingService', () {
    test('track() no bloquea: vuelve antes de que termine la llamada de red', () {
      final completerRed = Completer<void>();
      final dio = Dio(BaseOptions(baseUrl: 'http://test'));
      dio.httpClientAdapter = _AdaptadorFalso((options) async {
        await completerRed.future; // la red "nunca" responde en este test
        return _json('{}', 200);
      });

      final servicio = TrackingService(dio);

      final antes = DateTime.now();
      servicio.track(tipo: TipoEvento.vista, productoId: 1);
      final despues = DateTime.now();

      // Si track() hubiera esperado la red, esto tardaría para siempre
      // (el completer nunca se completa). Como vuelve al toque, queda
      // probado que es fire-and-forget.
      expect(despues.difference(antes).inMilliseconds, lessThan(50));
      expect(servicio.eventosEncolados, 1);

      completerRed.complete(); // libera el mock para no dejar un future colgado
    });

    test('si el endpoint no existe (404), el evento queda encolado y no se lanza excepción', () async {
      final dio = Dio(BaseOptions(baseUrl: 'http://test'));
      dio.httpClientAdapter = _AdaptadorFalso((options) async {
        return _json('{"detail":"Not Found"}', 404);
      });

      final servicio = TrackingService(dio);

      expect(() => servicio.track(tipo: TipoEvento.busqueda, texto: 'camisa'), returnsNormally);
      await Future<void>.delayed(const Duration(milliseconds: 50));

      expect(servicio.eventosEncolados, 1);
    });

    test('si el envío tiene éxito, el evento se saca de la cola', () async {
      var llamadas = 0;
      final dio = Dio(BaseOptions(baseUrl: 'http://test'));
      dio.httpClientAdapter = _AdaptadorFalso((options) async {
        llamadas++;
        return _json('{}', 200);
      });

      final servicio = TrackingService(dio);
      servicio.track(tipo: TipoEvento.favorito, varianteId: 7);
      await Future<void>.delayed(const Duration(milliseconds: 50));

      expect(llamadas, 1);
      expect(servicio.eventosEncolados, 0);
    });

    test('un evento nuevo también intenta vaciar los que ya estaban encolados', () async {
      var falla = true;
      final dio = Dio(BaseOptions(baseUrl: 'http://test'));
      dio.httpClientAdapter = _AdaptadorFalso((options) async {
        if (falla) return _json('{}', 404);
        return _json('{}', 200);
      });

      final servicio = TrackingService(dio);
      servicio.track(tipo: TipoEvento.vista, productoId: 1);
      await Future<void>.delayed(const Duration(milliseconds: 50));
      expect(servicio.eventosEncolados, 1);

      falla = false; // "se recupera la red" / "ya existe el endpoint"
      servicio.track(tipo: TipoEvento.vista, productoId: 2);
      await Future<void>.delayed(const Duration(milliseconds: 50));

      expect(servicio.eventosEncolados, 0);
    });
  });
}
