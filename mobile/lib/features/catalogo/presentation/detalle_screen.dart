import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/theme/app_theme.dart';
import '../../favoritos/state/favoritos_controller.dart';
import '../../tracking/models/evento.dart';
import '../../tracking/state/tracking_service.dart';
import '../models/catalogo_detalle.dart';
import '../state/catalogo_providers.dart';

class DetalleScreen extends ConsumerStatefulWidget {
  const DetalleScreen({required this.productoId, super.key});

  final int productoId;

  @override
  ConsumerState<DetalleScreen> createState() => _DetalleScreenState();
}

class _DetalleScreenState extends ConsumerState<DetalleScreen> {
  int? _tallaId;
  int? _colorId;
  bool _trackeado = false;

  @override
  Widget build(BuildContext context) {
    final asyncDetalle = ref.watch(detalleProductoProvider(widget.productoId));

    return Scaffold(
      backgroundColor: AppColors.fondo,
      appBar: AppBar(title: const Text('Detalle')),
      body: asyncDetalle.when(
        loading: () => const Center(child: CircularProgressIndicator(color: AppColors.acento)),
        error: (error, stack) => const Center(child: Text('No se pudo cargar la prenda.')),
        data: (detalle) {
          if (!_trackeado) {
            _trackeado = true;
            // Se registra una sola vez por entrada a la pantalla, después
            // del primer build (no bloquea la UI: es fire-and-forget).
            WidgetsBinding.instance.addPostFrameCallback((_) {
              ref.read(trackingServiceProvider).track(tipo: TipoEvento.vista, productoId: detalle.id);
            });
          }
          return _Contenido(detalle: detalle, tallaId: _tallaId, colorId: _colorId, onSeleccion: _seleccionar);
        },
      ),
    );
  }

  void _seleccionar({int? tallaId, int? colorId}) {
    setState(() {
      if (tallaId != null) _tallaId = tallaId;
      if (colorId != null) _colorId = colorId;
    });
  }
}

class _Contenido extends ConsumerWidget {
  const _Contenido({required this.detalle, required this.tallaId, required this.colorId, required this.onSeleccion});

  final CatalogoDetalle detalle;
  final int? tallaId;
  final int? colorId;
  final void Function({int? tallaId, int? colorId}) onSeleccion;

  VarianteCatalogo? get _varianteActiva {
    if (tallaId == null || colorId == null) return null;
    for (final v in detalle.variantes) {
      if (v.tallaId == tallaId && v.colorId == colorId) return v;
    }
    return null;
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final tallasIds = detalle.variantes.map((v) => v.tallaId).toSet();
    final coloresIds = detalle.variantes.map((v) => v.colorId).toSet();
    final variante = _varianteActiva;
    final precio = variante?.precioEfectivo ?? detalle.precioBase;

    return ListView(
      padding: const EdgeInsets.only(bottom: AppSpacing.xl),
      children: [
        _Carrusel(imagenes: detalle.imagenes),
        Padding(
          padding: const EdgeInsets.all(AppSpacing.lg),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Expanded(
                    child: Text(detalle.nombre, style: Theme.of(context).textTheme.headlineMedium),
                  ),
                  if (variante != null) _BotonFavorito(varianteId: variante.id),
                ],
              ),
              const SizedBox(height: AppSpacing.xs),
              Text(
                'Bs ${precio.toStringAsFixed(2)}',
                style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w700, color: AppColors.acento),
              ),
              const SizedBox(height: AppSpacing.lg),

              const Text('Talla', style: TextStyle(color: AppColors.textoTenue, fontSize: 12)),
              const SizedBox(height: AppSpacing.xs),
              Consumer(
                builder: (context, ref, _) {
                  final asyncTallas = ref.watch(tallasRefProvider);
                  return asyncTallas.when(
                    loading: () => const SizedBox.shrink(),
                    error: (e, s) => const SizedBox.shrink(),
                    data: (tallas) => Wrap(
                      spacing: AppSpacing.sm,
                      children: [
                        for (final t in tallas.where((t) => tallasIds.contains(t.id)))
                          ChoiceChip(
                            label: Text(t.codigo),
                            selected: tallaId == t.id,
                            onSelected: (_) => onSeleccion(tallaId: t.id),
                          ),
                      ],
                    ),
                  );
                },
              ),
              const SizedBox(height: AppSpacing.md),

              const Text('Color', style: TextStyle(color: AppColors.textoTenue, fontSize: 12)),
              const SizedBox(height: AppSpacing.xs),
              Consumer(
                builder: (context, ref, _) {
                  final asyncColores = ref.watch(coloresRefProvider);
                  return asyncColores.when(
                    loading: () => const SizedBox.shrink(),
                    error: (e, s) => const SizedBox.shrink(),
                    data: (colores) => Wrap(
                      spacing: AppSpacing.sm,
                      children: [
                        for (final c in colores.where((c) => coloresIds.contains(c.id)))
                          ChoiceChip(
                            label: Text(c.nombre),
                            selected: colorId == c.id,
                            onSelected: (_) => onSeleccion(colorId: c.id),
                          ),
                      ],
                    ),
                  );
                },
              ),

              if (tallaId != null && colorId != null && variante == null) ...[
                const SizedBox(height: AppSpacing.md),
                const Text(
                  'Esa combinación de talla y color no está disponible.',
                  style: TextStyle(color: AppColors.error),
                ),
              ],

              if (detalle.descripcion != null && detalle.descripcion!.isNotEmpty) ...[
                const SizedBox(height: AppSpacing.lg),
                const Text('Descripción', style: TextStyle(color: AppColors.textoTenue, fontSize: 12)),
                const SizedBox(height: AppSpacing.xs),
                Text(detalle.descripcion!),
              ],

              const SizedBox(height: AppSpacing.lg),
              const Text('Disponibilidad por sucursal', style: TextStyle(color: AppColors.textoTenue, fontSize: 12)),
              const SizedBox(height: AppSpacing.xs),
              const _DisponibilidadPorSucursal(),
            ],
          ),
        ),
      ],
    );
  }
}

class _Carrusel extends StatelessWidget {
  const _Carrusel({required this.imagenes});

  final List<ImagenProducto> imagenes;

  @override
  Widget build(BuildContext context) {
    if (imagenes.isEmpty) {
      return Container(
        height: 320,
        color: AppColors.fondoAlterno,
        child: const Icon(Icons.checkroom, size: 64, color: AppColors.textoTenue),
      );
    }

    return SizedBox(
      height: 320,
      child: PageView.builder(
        itemCount: imagenes.length,
        itemBuilder: (context, index) {
          return CachedNetworkImage(
            imageUrl: imagenes[index].url,
            fit: BoxFit.cover,
            placeholder: (context, url) => Container(color: AppColors.fondoAlterno),
          );
        },
      ),
    );
  }
}

class _BotonFavorito extends ConsumerWidget {
  const _BotonFavorito({required this.varianteId});

  final int varianteId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final controller = ref.watch(favoritosControllerProvider.notifier);
    final esFavorito = ref.watch(favoritosControllerProvider).maybeWhen(
          data: (_) => controller.esFavorito(varianteId),
          orElse: () => false,
        );

    return IconButton(
      icon: Icon(esFavorito ? Icons.favorite : Icons.favorite_border, color: AppColors.error),
      onPressed: () => controller.alternar(varianteId),
    );
  }
}

class _DisponibilidadPorSucursal extends ConsumerWidget {
  const _DisponibilidadPorSucursal();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final asyncSucursales = ref.watch(sucursalesRefProvider);

    return asyncSucursales.when(
      loading: () => const LinearProgressIndicator(),
      error: (e, s) => const Text('No se pudo cargar la lista de sucursales.'),
      data: (sucursales) => Column(
        children: [
          for (final sucursal in sucursales)
            ListTile(
              contentPadding: EdgeInsets.zero,
              leading: const Icon(Icons.storefront_outlined, color: AppColors.textoTenue),
              title: Text(sucursal.nombre),
              // TODO(P3.1): hoy el backend todavía no calcula stock real
              // por sucursal (paquete `inventario`). En cuanto exista, acá
              // se muestra disponible/agotado real en vez de este texto.
              trailing: const Text('Consultar en tienda', style: TextStyle(color: AppColors.textoTenue, fontSize: 12)),
            ),
        ],
      ),
    );
  }
}
