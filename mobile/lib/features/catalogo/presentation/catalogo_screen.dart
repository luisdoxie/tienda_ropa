import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_theme.dart';
import '../../auth/state/auth_controller.dart';
import '../models/catalogo_item.dart';
import '../models/filtros_catalogo.dart';
import '../state/catalogo_controller.dart';
import 'filtros_sheet.dart';

class CatalogoScreen extends ConsumerStatefulWidget {
  const CatalogoScreen({super.key});

  @override
  ConsumerState<CatalogoScreen> createState() => _CatalogoScreenState();
}

class _CatalogoScreenState extends ConsumerState<CatalogoScreen> {
  final _scrollController = ScrollController();
  final _busquedaController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _scrollController.addListener(_onScroll);
  }

  @override
  void dispose() {
    _scrollController.removeListener(_onScroll);
    _scrollController.dispose();
    _busquedaController.dispose();
    super.dispose();
  }

  void _onScroll() {
    // Scroll infinito: al acercarse al final, pide la próxima página.
    final faltaPoco = _scrollController.position.pixels >= _scrollController.position.maxScrollExtent - 400;
    if (faltaPoco) {
      ref.read(catalogoControllerProvider.notifier).cargarSiguientePagina();
    }
  }

  Future<void> _abrirFiltros() async {
    final filtrosActuales = ref.read(catalogoControllerProvider).filtros;
    final nuevosFiltros = await showModalBottomSheet<FiltrosCatalogo>(
      context: context,
      isScrollControlled: true,
      builder: (context) => FiltrosSheet(filtrosIniciales: filtrosActuales),
    );
    if (nuevosFiltros != null) {
      await ref.read(catalogoControllerProvider.notifier).aplicarFiltros(nuevosFiltros);
    }
  }

  void _buscar(String texto) {
    final actuales = ref.read(catalogoControllerProvider).filtros;
    ref.read(catalogoControllerProvider.notifier).aplicarFiltros(actuales.copyWith(texto: texto));
  }

  @override
  Widget build(BuildContext context) {
    final estado = ref.watch(catalogoControllerProvider);

    return Scaffold(
      backgroundColor: AppColors.fondo,
      appBar: AppBar(
        title: const Text('FashionStore'),
        actions: [
          IconButton(
            icon: const Icon(Icons.accessibility_new_outlined),
            tooltip: 'Probador (detección de pose)',
            onPressed: () => context.push('/probador/pose'),
          ),
          IconButton(
            icon: const Icon(Icons.favorite_border),
            tooltip: 'Favoritos',
            onPressed: () => context.push('/favoritos'),
          ),
          IconButton(
            icon: const Icon(Icons.calendar_month_outlined),
            tooltip: 'Mis reservas',
            onPressed: () => context.push('/reservas'),
          ),
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: 'Cerrar sesión',
            onPressed: () => ref.read(authControllerProvider.notifier).logout(),
          ),
        ],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(AppSpacing.md, AppSpacing.md, AppSpacing.md, 0),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _busquedaController,
                    decoration: const InputDecoration(
                      hintText: 'Buscar prendas...',
                      prefixIcon: Icon(Icons.search),
                    ),
                    textInputAction: TextInputAction.search,
                    onSubmitted: _buscar,
                  ),
                ),
                const SizedBox(width: AppSpacing.sm),
                IconButton.filledTonal(
                  icon: Icon(estado.filtros.tieneFiltros ? Icons.filter_alt : Icons.filter_alt_outlined),
                  tooltip: 'Filtros',
                  onPressed: _abrirFiltros,
                ),
              ],
            ),
          ),
          Expanded(child: _Contenido(estado: estado, scrollController: _scrollController)),
        ],
      ),
    );
  }
}

class _Contenido extends StatelessWidget {
  const _Contenido({required this.estado, required this.scrollController});

  final CatalogoState estado;
  final ScrollController scrollController;

  @override
  Widget build(BuildContext context) {
    if (estado.cargandoPrimeraPagina) {
      return const Center(child: CircularProgressIndicator(color: AppColors.acento));
    }

    if (estado.error && estado.items.isEmpty) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(AppSpacing.xl),
          child: Text('No se pudo cargar el catálogo. Deslizá para reintentar.', textAlign: TextAlign.center),
        ),
      );
    }

    if (estado.items.isEmpty) {
      return const Center(child: Text('No se encontraron prendas.', style: TextStyle(color: AppColors.textoTenue)));
    }

    return GridView.builder(
      controller: scrollController,
      padding: const EdgeInsets.all(AppSpacing.md),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        mainAxisSpacing: AppSpacing.md,
        crossAxisSpacing: AppSpacing.md,
        childAspectRatio: 0.68,
      ),
      itemCount: estado.items.length + (estado.hayMas ? 1 : 0),
      itemBuilder: (context, index) {
        if (index >= estado.items.length) {
          return const Center(child: CircularProgressIndicator(color: AppColors.acento));
        }
        return _TarjetaProducto(item: estado.items[index]);
      },
    );
  }
}

class _TarjetaProducto extends StatelessWidget {
  const _TarjetaProducto({required this.item});

  final CatalogoItem item;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () => context.push('/producto/${item.id}'),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: ClipRRect(
              borderRadius: BorderRadius.circular(AppRadius.base),
              child: item.imagenPrincipal != null
                  ? CachedNetworkImage(
                      imageUrl: item.imagenPrincipal!,
                      fit: BoxFit.cover,
                      width: double.infinity,
                      placeholder: (context, url) => Container(color: AppColors.fondoAlterno),
                      errorWidget: (context, url, error) => Container(
                        color: AppColors.fondoAlterno,
                        child: const Icon(Icons.checkroom, color: AppColors.textoTenue),
                      ),
                    )
                  : Container(
                      color: AppColors.fondoAlterno,
                      child: const Icon(Icons.checkroom, color: AppColors.textoTenue),
                    ),
            ),
          ),
          const SizedBox(height: AppSpacing.xs),
          Text(item.nombre, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 14)),
          Text(
            'Bs ${item.precioBase.toStringAsFixed(2)}',
            style: const TextStyle(fontWeight: FontWeight.w600, color: AppColors.acento),
          ),
        ],
      ),
    );
  }
}
