import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/network/providers.dart';
import '../../tracking/models/evento.dart';
import '../../tracking/state/tracking_service.dart';
import '../data/favoritos_repository.dart';
import '../models/favorito.dart';

final favoritosRepositoryProvider = Provider<FavoritosRepository>(
  (ref) => FavoritosRepository(ref.watch(dioProvider)),
);

class FavoritosController extends StateNotifier<AsyncValue<List<Favorito>>> {
  FavoritosController(this._ref) : super(const AsyncValue.loading()) {
    cargar();
  }

  final Ref _ref;

  FavoritosRepository get _repo => _ref.read(favoritosRepositoryProvider);

  Future<void> cargar() async {
    state = const AsyncValue.loading();
    try {
      state = AsyncValue.data(await _repo.listar());
    } catch (error, stackTrace) {
      state = AsyncValue.error(error, stackTrace);
    }
  }

  bool esFavorito(int varianteId) => state.value?.any((f) => f.varianteId == varianteId) ?? false;

  Future<void> alternar(int varianteId) async {
    final yaEsFavorito = esFavorito(varianteId);
    if (yaEsFavorito) {
      await _repo.quitar(varianteId);
    } else {
      await _repo.agregar(varianteId);
      _ref.read(trackingServiceProvider).track(tipo: TipoEvento.favorito, varianteId: varianteId);
    }
    await cargar();
  }
}

final favoritosControllerProvider = StateNotifierProvider<FavoritosController, AsyncValue<List<Favorito>>>(
  (ref) => FavoritosController(ref),
);
