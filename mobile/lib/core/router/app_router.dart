import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../features/auth/presentation/login_screen.dart';
import '../../features/auth/presentation/registro_screen.dart';
import '../../features/auth/state/auth_controller.dart';
import '../../features/auth/state/auth_state.dart';
import '../../features/catalogo/presentation/catalogo_screen.dart';
import '../../features/catalogo/presentation/detalle_screen.dart';
import '../../features/favoritos/presentation/favoritos_screen.dart';
import '../../features/probador/presentation/probador_screen.dart';
import '../../features/reservas/presentation/confirmar_reserva_screen.dart';
import '../../features/reservas/presentation/mis_reservas_screen.dart';
import '../../features/reservas/presentation/reserva_detalle_screen.dart';
import '../../features/splash/presentation/splash_screen.dart';

class _RefrescoDelRouter extends ChangeNotifier {
  _RefrescoDelRouter(Ref ref) {
    ref.listen<AuthState>(authControllerProvider, (_, _) => notifyListeners());
  }
}

final _refrescoDelRouterProvider = Provider<_RefrescoDelRouter>((ref) => _RefrescoDelRouter(ref));

final routerProvider = Provider<GoRouter>((ref) {
  final refresco = ref.watch(_refrescoDelRouterProvider);

  return GoRouter(
    initialLocation: '/splash',
    refreshListenable: refresco,
    redirect: (context, state) {
      final authState = ref.read(authControllerProvider);
      final ruta = state.matchedLocation;
      final esRutaPublica = ruta == '/login' || ruta == '/registro';
      final esSplash = ruta == '/splash';

      switch (authState.estado) {
        case EstadoSesion.inicial:
        case EstadoSesion.cargando:
          return esSplash ? null : '/splash';
        case EstadoSesion.noAutenticado:
          return esRutaPublica ? null : '/login';
        case EstadoSesion.autenticado:
          return (esRutaPublica || esSplash) ? '/home' : null;
      }
    },
    routes: [
      GoRoute(path: '/splash', builder: (context, state) => const SplashScreen()),
      GoRoute(path: '/login', builder: (context, state) => const LoginScreen()),
      GoRoute(path: '/registro', builder: (context, state) => const RegistroScreen()),
      GoRoute(path: '/home', builder: (context, state) => const CatalogoScreen()),
      GoRoute(
        path: '/producto/:id',
        builder: (context, state) => DetalleScreen(productoId: int.parse(state.pathParameters['id']!)),
      ),
      GoRoute(path: '/favoritos', builder: (context, state) => const FavoritosScreen()),
      GoRoute(path: '/probador', builder: (context, state) => const ProbadorScreen()),
      GoRoute(path: '/reserva/confirmar', builder: (context, state) => const ConfirmarReservaScreen()),
      GoRoute(path: '/reservas', builder: (context, state) => const MisReservasScreen()),
      GoRoute(
        path: '/reserva/:id',
        builder: (context, state) => ReservaDetalleScreen(reservaId: int.parse(state.pathParameters['id']!)),
      ),
    ],
  );
});
