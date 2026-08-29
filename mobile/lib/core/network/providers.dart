import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'dio_client.dart';
import 'token_storage.dart';

final tokenStorageProvider = Provider<TokenStorage>((ref) => const TokenStorage());

/// Se incrementa cuando el interceptor de Dio no pudo refrescar el token
/// (el refresh token también venció). authControllerProvider escucha esto
/// para cerrar la sesión de verdad, sin que dioProvider tenga que conocer
/// a authControllerProvider (evita un ciclo de providers).
final sesionExpiradaProvider = StateProvider<int>((ref) => 0);

final dioProvider = Provider<Dio>((ref) {
  final tokenStorage = ref.watch(tokenStorageProvider);
  return buildDio(
    tokenStorage: tokenStorage,
    onSesionExpirada: () async {
      ref.read(sesionExpiradaProvider.notifier).state++;
    },
  );
});
