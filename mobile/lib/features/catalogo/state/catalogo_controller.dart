import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../features/tracking/models/evento.dart';
import '../../../features/tracking/state/tracking_service.dart';
import '../models/catalogo_item.dart';
import '../models/filtros_catalogo.dart';
import 'catalogo_providers.dart';

class CatalogoState {
  const CatalogoState({
    this.items = const [],
    this.pagina = 1,
    this.cargando = false,
    this.cargandoPrimeraPagina = true,
    this.hayMas = true,
    this.error = false,
    this.filtros = const FiltrosCatalogo(),
  });

  final List<CatalogoItem> items;
  final int pagina;
  final bool cargando;
  final bool cargandoPrimeraPagina;
  final bool hayMas;
  final bool error;
  final FiltrosCatalogo filtros;

  CatalogoState copyWith({
    List<CatalogoItem>? items,
    int? pagina,
    bool? cargando,
    bool? cargandoPrimeraPagina,
    bool? hayMas,
    bool? error,
    FiltrosCatalogo? filtros,
  }) {
    return CatalogoState(
      items: items ?? this.items,
      pagina: pagina ?? this.pagina,
      cargando: cargando ?? this.cargando,
      cargandoPrimeraPagina: cargandoPrimeraPagina ?? this.cargandoPrimeraPagina,
      hayMas: hayMas ?? this.hayMas,
      error: error ?? false,
      filtros: filtros ?? this.filtros,
    );
  }
}

class CatalogoController extends StateNotifier<CatalogoState> {
  CatalogoController(this._ref) : super(const CatalogoState()) {
    cargarPrimeraPagina();
  }

  final Ref _ref;
  static const _tamanioPagina = 20;

  Future<void> cargarPrimeraPagina() async {
    state = state.copyWith(cargandoPrimeraPagina: true, error: false);
    try {
      final items = await _obtenerPagina(1);
      state = state.copyWith(
        items: items,
        pagina: 1,
        hayMas: items.length == _tamanioPagina,
        cargandoPrimeraPagina: false,
      );
    } catch (_) {
      state = state.copyWith(cargandoPrimeraPagina: false, error: true);
    }
  }

  Future<void> cargarSiguientePagina() async {
    if (state.cargando || state.cargandoPrimeraPagina || !state.hayMas) return;

    state = state.copyWith(cargando: true);
    try {
      final siguiente = state.pagina + 1;
      final nuevos = await _obtenerPagina(siguiente);
      state = state.copyWith(
        items: [...state.items, ...nuevos],
        pagina: siguiente,
        hayMas: nuevos.length == _tamanioPagina,
        cargando: false,
      );
    } catch (_) {
      // Si falla al pedir "una página más", no se rompe la grilla que ya
      // se veía: se deja de cargar y listo.
      state = state.copyWith(cargando: false);
    }
  }

  Future<void> aplicarFiltros(FiltrosCatalogo filtros) async {
    state = state.copyWith(filtros: filtros);
    await cargarPrimeraPagina();

    if (filtros.texto != null && filtros.texto!.isNotEmpty) {
      _ref.read(trackingServiceProvider).track(tipo: TipoEvento.busqueda, texto: filtros.texto);
    }
  }

  Future<void> limpiarFiltros() => aplicarFiltros(const FiltrosCatalogo());

  Future<List<CatalogoItem>> _obtenerPagina(int pagina) {
    final repo = _ref.read(catalogoRepositoryProvider);
    if (state.filtros.tieneFiltros) {
      return repo.buscar(state.filtros, pagina: pagina, tamanio: _tamanioPagina);
    }
    return repo.listar(pagina: pagina, tamanio: _tamanioPagina);
  }
}

final catalogoControllerProvider = StateNotifierProvider<CatalogoController, CatalogoState>(
  (ref) => CatalogoController(ref),
);
