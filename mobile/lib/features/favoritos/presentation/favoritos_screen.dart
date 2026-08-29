import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_theme.dart';
import '../state/favoritos_controller.dart';

class FavoritosScreen extends ConsumerWidget {
  const FavoritosScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final asyncFavoritos = ref.watch(favoritosControllerProvider);

    return Scaffold(
      backgroundColor: AppColors.fondo,
      appBar: AppBar(title: const Text('Mis favoritos')),
      body: asyncFavoritos.when(
        loading: () => const Center(child: CircularProgressIndicator(color: AppColors.acento)),
        error: (error, stack) => const Center(child: Text('No se pudieron cargar los favoritos.')),
        data: (favoritos) {
          if (favoritos.isEmpty) {
            return const Center(
              child: Text('Todavía no tenés favoritos.', style: TextStyle(color: AppColors.textoTenue)),
            );
          }
          return ListView.separated(
            padding: const EdgeInsets.all(AppSpacing.md),
            itemCount: favoritos.length,
            separatorBuilder: (context, index) => const Divider(height: 1, color: AppColors.borde),
            itemBuilder: (context, index) {
              final favorito = favoritos[index];
              return ListTile(
                leading: const Icon(Icons.favorite, color: AppColors.error),
                title: Text(favorito.nombreProducto),
                subtitle: Text(favorito.sku, style: const TextStyle(color: AppColors.textoTenue)),
                onTap: () => context.push('/producto/${favorito.productoId}'),
                trailing: IconButton(
                  icon: const Icon(Icons.close),
                  onPressed: () => ref.read(favoritosControllerProvider.notifier).alternar(favorito.varianteId),
                ),
              );
            },
          );
        },
      ),
    );
  }
}
