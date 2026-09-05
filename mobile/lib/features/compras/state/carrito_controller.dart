import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/carrito.dart';
import 'compras_providers.dart';

class CarritoController extends StateNotifier<AsyncValue<Carrito>> {
  CarritoController(this._ref) : super(const AsyncValue.loading()) {
    cargar();
  }

  final Ref _ref;

  Future<void> cargar() async {
    state = const AsyncValue.loading();
    try {
      state = AsyncValue.data(await _conExhibicion(await _ref.read(carritoRepositoryProvider).obtener()));
    } catch (error, stackTrace) {
      state = AsyncValue.error(error, stackTrace);
    }
  }

  Future<void> agregar({required int varianteId, required int cantidad}) async {
    final carrito = await _ref
        .read(carritoRepositoryProvider)
        .agregar(varianteId: varianteId, cantidad: cantidad);
    state = AsyncValue.data(await _conExhibicion(carrito));
  }

  Future<void> actualizarCantidad({required int varianteId, required int cantidad}) async {
    final carrito = await _ref
        .read(carritoRepositoryProvider)
        .actualizarCantidad(varianteId: varianteId, cantidad: cantidad);
    state = AsyncValue.data(await _conExhibicion(carrito));
  }

  Future<void> quitar(int varianteId) async {
    final carrito = await _ref.read(carritoRepositoryProvider).quitar(varianteId);
    state = AsyncValue.data(await _conExhibicion(carrito));
  }

  Future<Carrito> _conExhibicion(Carrito carrito) async {
    if (carrito.detalle.isEmpty) return carrito;
    final porVariante = await lookupVariantes(_ref, carrito.detalle.map((l) => l.varianteId).toList());
    final detalleResuelto = carrito.detalle.map((linea) {
      final item = porVariante[linea.varianteId];
      return linea.conExhibicion(
        productoNombre: item?.productoNombre,
        imagenPrincipal: item?.imagenPrincipal,
        tallaCodigo: item?.tallaCodigo,
        colorNombre: item?.colorNombre,
      );
    }).toList();
    return carrito.conDetalle(detalleResuelto);
  }
}

final carritoControllerProvider = StateNotifierProvider<CarritoController, AsyncValue<Carrito>>(
  (ref) => CarritoController(ref),
);
