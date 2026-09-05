import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../data/ventas_repository.dart';
import '../models/venta.dart';
import 'compras_providers.dart';

class MisComprasController extends StateNotifier<AsyncValue<List<Venta>>> {
  MisComprasController(this._ref) : super(const AsyncValue.loading()) {
    cargar();
  }

  final Ref _ref;

  VentasRepository get _repo => _ref.read(ventasRepositoryProvider);

  Future<void> cargar() async {
    state = const AsyncValue.loading();
    try {
      state = AsyncValue.data(await _repo.misCompras());
    } catch (error, stackTrace) {
      state = AsyncValue.error(error, stackTrace);
    }
  }
}

final misComprasControllerProvider = StateNotifierProvider<MisComprasController, AsyncValue<List<Venta>>>(
  (ref) => MisComprasController(ref),
);
