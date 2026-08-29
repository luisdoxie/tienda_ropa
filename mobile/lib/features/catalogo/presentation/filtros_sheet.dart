import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/theme/app_theme.dart';
import '../models/filtros_catalogo.dart';
import '../state/catalogo_providers.dart';

const _generos = [
  (valor: 'hombre', etiqueta: 'Hombre'),
  (valor: 'mujer', etiqueta: 'Mujer'),
  (valor: 'unisex', etiqueta: 'Unisex'),
  (valor: 'nino', etiqueta: 'Niño'),
];

class FiltrosSheet extends ConsumerStatefulWidget {
  const FiltrosSheet({required this.filtrosIniciales, super.key});

  final FiltrosCatalogo filtrosIniciales;

  @override
  ConsumerState<FiltrosSheet> createState() => _FiltrosSheetState();
}

class _FiltrosSheetState extends ConsumerState<FiltrosSheet> {
  late FiltrosCatalogo _filtros;
  late final TextEditingController _precioMinController;
  late final TextEditingController _precioMaxController;

  @override
  void initState() {
    super.initState();
    _filtros = widget.filtrosIniciales;
    _precioMinController = TextEditingController(text: _filtros.precioMin?.toStringAsFixed(0) ?? '');
    _precioMaxController = TextEditingController(text: _filtros.precioMax?.toStringAsFixed(0) ?? '');
  }

  @override
  void dispose() {
    _precioMinController.dispose();
    _precioMaxController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return DraggableScrollableSheet(
      initialChildSize: 0.75,
      minChildSize: 0.4,
      maxChildSize: 0.95,
      expand: false,
      builder: (context, scrollController) {
        return Padding(
          padding: const EdgeInsets.all(AppSpacing.lg),
          child: ListView(
            controller: scrollController,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text('Filtros', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w600)),
                  TextButton(
                    onPressed: () => setState(() => _filtros = const FiltrosCatalogo()),
                    child: const Text('Limpiar'),
                  ),
                ],
              ),
              const SizedBox(height: AppSpacing.md),

              _SelectorReferencia(
                etiqueta: 'Categoría',
                provider: categoriasRefProvider,
                nombreDe: (c) => c.nombre,
                idDe: (c) => c.id,
                seleccionado: _filtros.categoriaId,
                onChanged: (id) => setState(() => _filtros = _filtros.copyWith(categoriaId: id, limpiarCategoria: id == null)),
              ),
              _SelectorReferencia(
                etiqueta: 'Talla',
                provider: tallasRefProvider,
                nombreDe: (t) => t.codigo,
                idDe: (t) => t.id,
                seleccionado: _filtros.tallaId,
                onChanged: (id) => setState(() => _filtros = _filtros.copyWith(tallaId: id, limpiarTalla: id == null)),
              ),
              _SelectorReferencia(
                etiqueta: 'Color',
                provider: coloresRefProvider,
                nombreDe: (c) => c.nombre,
                idDe: (c) => c.id,
                seleccionado: _filtros.colorId,
                onChanged: (id) => setState(() => _filtros = _filtros.copyWith(colorId: id, limpiarColor: id == null)),
              ),
              _SelectorReferencia(
                etiqueta: 'Material',
                provider: materialesRefProvider,
                nombreDe: (m) => m.nombre,
                idDe: (m) => m.id,
                seleccionado: _filtros.materialId,
                onChanged: (id) => setState(() => _filtros = _filtros.copyWith(materialId: id, limpiarMaterial: id == null)),
              ),
              _SelectorReferencia(
                etiqueta: 'Temporada',
                provider: temporadasRefProvider,
                nombreDe: (t) => '${t.nombre} ${t.anio}',
                idDe: (t) => t.id,
                seleccionado: _filtros.temporadaId,
                onChanged: (id) => setState(() => _filtros = _filtros.copyWith(temporadaId: id, limpiarTemporada: id == null)),
              ),

              const SizedBox(height: AppSpacing.sm),
              const Text('Género', style: TextStyle(color: AppColors.textoTenue, fontSize: 12)),
              Wrap(
                spacing: AppSpacing.sm,
                children: [
                  for (final genero in _generos)
                    ChoiceChip(
                      label: Text(genero.etiqueta),
                      selected: _filtros.genero == genero.valor,
                      onSelected: (seleccionado) => setState(
                        () => _filtros = _filtros.copyWith(
                          genero: seleccionado ? genero.valor : null,
                          limpiarGenero: !seleccionado,
                        ),
                      ),
                    ),
                ],
              ),

              const SizedBox(height: AppSpacing.md),
              const Text('Precio', style: TextStyle(color: AppColors.textoTenue, fontSize: 12)),
              Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _precioMinController,
                      keyboardType: TextInputType.number,
                      decoration: const InputDecoration(hintText: 'Mín.'),
                    ),
                  ),
                  const SizedBox(width: AppSpacing.sm),
                  Expanded(
                    child: TextField(
                      controller: _precioMaxController,
                      keyboardType: TextInputType.number,
                      decoration: const InputDecoration(hintText: 'Máx.'),
                    ),
                  ),
                ],
              ),

              const SizedBox(height: AppSpacing.xl),
              ElevatedButton(
                onPressed: () {
                  final precioMin = double.tryParse(_precioMinController.text);
                  final precioMax = double.tryParse(_precioMaxController.text);
                  Navigator.of(context).pop(
                    _filtros.copyWith(
                      precioMin: precioMin,
                      precioMax: precioMax,
                      limpiarPrecioMin: precioMin == null,
                      limpiarPrecioMax: precioMax == null,
                    ),
                  );
                },
                child: const Text('Aplicar filtros'),
              ),
            ],
          ),
        );
      },
    );
  }
}

class _SelectorReferencia<T> extends ConsumerWidget {
  const _SelectorReferencia({
    required this.etiqueta,
    required this.provider,
    required this.nombreDe,
    required this.idDe,
    required this.seleccionado,
    required this.onChanged,
  });

  final String etiqueta;
  final FutureProvider<List<T>> provider;
  final String Function(T) nombreDe;
  final int Function(T) idDe;
  final int? seleccionado;
  final ValueChanged<int?> onChanged;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final asyncItems = ref.watch(provider);

    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.sm),
      child: asyncItems.when(
        loading: () => const LinearProgressIndicator(),
        error: (error, stack) => Text('No se pudo cargar $etiqueta', style: const TextStyle(color: AppColors.error)),
        data: (items) => DropdownButtonFormField<int?>(
          initialValue: seleccionado,
          decoration: InputDecoration(labelText: etiqueta),
          items: [
            const DropdownMenuItem<int?>(value: null, child: Text('Cualquiera')),
            for (final item in items) DropdownMenuItem<int?>(value: idDe(item), child: Text(nombreDe(item))),
          ],
          onChanged: onChanged,
        ),
      ),
    );
  }
}
