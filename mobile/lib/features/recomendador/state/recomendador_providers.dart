import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/network/providers.dart';
import '../data/recomendador_repository.dart';
import '../models/recomendacion_item.dart';

final recomendadorRepositoryProvider = Provider<RecomendadorRepository>(
  (ref) => RecomendadorRepository(ref.watch(dioProvider)),
);

/// Carrusel del home: recomendaciones generales del cliente (o de
/// popularidad, si es anónimo/nuevo).
final recomendacionesHomeProvider = FutureProvider<List<RecomendacionItem>>(
  (ref) => ref.watch(recomendadorRepositoryProvider).obtenerRecomendaciones(),
);

/// Carrusel del detalle de una prenda: mismas recomendaciones, excluyendo
/// el producto que se está viendo.
final recomendacionesDetalleProvider = FutureProvider.family<List<RecomendacionItem>, int>(
  (ref, productoId) => ref.watch(recomendadorRepositoryProvider).obtenerRecomendaciones(excluirProductoId: productoId),
);
