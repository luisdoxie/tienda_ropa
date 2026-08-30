import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/providers.dart';
import '../../catalogo/state/catalogo_providers.dart';
import '../data/probador_repository.dart';
import '../models/activo_probador.dart';

final probadorRepositoryProvider = Provider<ProbadorRepository>(
  (ref) => ProbadorRepository(ref.watch(dioProvider)),
);

class PrendaProbador {
  const PrendaProbador({required this.varianteId, required this.nombre, required this.assets});

  final int varianteId;
  final String nombre;
  final AssetsVariante assets;
}

/// Recorre el catálogo buscando productos que admiten probador Y que ya
/// tienen un overlay validado: `admite_probador` es a nivel de producto,
/// pero el asset se sube por variante, así que no todo lo que admite
/// probador tiene ya la imagen lista. Lo que sí tiene se usa para llenar
/// el selector horizontal de la pantalla del probador.
final prendasProbadorProvider = FutureProvider<List<PrendaProbador>>((ref) async {
  final catalogoRepo = ref.watch(catalogoRepositoryProvider);
  final probadorRepo = ref.watch(probadorRepositoryProvider);

  final items = await catalogoRepo.listar(pagina: 1, tamanio: 50);
  final candidatos = items.where((i) => i.admiteProbador);

  final prendas = <PrendaProbador>[];
  for (final item in candidatos) {
    try {
      final detalle = await catalogoRepo.detalle(item.id);
      if (detalle.variantes.isEmpty) continue;
      final varianteId = detalle.variantes.first.id;
      final assets = await probadorRepo.obtenerAssets(varianteId);
      prendas.add(PrendaProbador(varianteId: varianteId, nombre: item.nombre, assets: assets));
    } catch (_) {
      // Sin overlay validado todavía para esta variante: no aparece en el selector.
      continue;
    }
  }
  return prendas;
});
