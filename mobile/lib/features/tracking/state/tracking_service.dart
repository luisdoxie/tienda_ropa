import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/network/providers.dart';
import '../models/evento.dart';

/// Registra eventos de navegación (vista, búsqueda, favorito) para
/// alimentar al recomendador. El endpoint real (POST /api/v1/ia/eventos)
/// todavía no existe -- llega en la etapa 6 -- así que hasta entonces cada
/// intento falla con 404 y el evento se queda encolado en memoria.
///
/// `track()` nunca lanza ni bloquea a quien lo llama: dispara el envío
/// sin esperarlo (fire-and-forget). Si falla la red o el endpoint no
/// existe, el error se traga acá adentro, nunca llega a la UI.
class TrackingService {
  TrackingService(this._dio);

  final Dio _dio;
  final List<Evento> _cola = [];

  int get eventosEncolados => _cola.length;

  void track({required TipoEvento tipo, int? productoId, int? varianteId, String? texto}) {
    _cola.add(
      Evento(tipo: tipo, productoId: productoId, varianteId: varianteId, texto: texto, creadoEn: DateTime.now()),
    );
    unawaited(_vaciarCola());
  }

  Future<void> _vaciarCola() async {
    // Copia porque _cola puede mutar mientras se recorre (otro track()
    // concurrente, o un elemento que se saca al confirmarse el envío).
    for (final evento in List<Evento>.from(_cola)) {
      try {
        await _dio.post<void>('/ia/eventos', data: evento.toJson());
        _cola.remove(evento);
      } catch (_) {
        // Sin conexión, o 404 porque el endpoint todavía no existe: se
        // deja encolado para el próximo intento, no se propaga el error.
        return;
      }
    }
  }
}

final trackingServiceProvider = Provider<TrackingService>((ref) => TrackingService(ref.watch(dioProvider)));
