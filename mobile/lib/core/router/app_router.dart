import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../features/auth/presentation/login_screen.dart';
import '../../features/auth/presentation/registro_screen.dart';
import '../../features/auth/state/auth_controller.dart';
import '../../features/auth/state/auth_state.dart';
import '../../features/catalogo/presentation/catalogo_screen.dart';
import '../../features/catalogo/presentation/detalle_screen.dart';
import '../../features/compras/presentation/carrito_screen.dart';
import '../../features/compras/presentation/compra_detalle_screen.dart';
import '../../features/compras/presentation/direccion_form_screen.dart';
import '../../features/compras/presentation/entrega_screen.dart';
import '../../features/compras/presentation/estado_pago_screen.dart';
import '../../features/compras/presentation/mis_compras_screen.dart';
import '../../features/compras/presentation/pago_screen.dart';
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

bool _esRutaAuth(String ruta) => ruta == '/login' || ruta == '/registro';

// El catálogo y el detalle de producto son públicos (igual que en el web,
// que solo protege carrito/checkout/mis-compras/reservas con authGuard).
// Todo lo demás cae en la rama "protegida" del redirect de abajo.
bool _esRutaPublicaParaInvitado(String ruta) => ruta == '/home' || ruta.startsWith('/producto/');

final routerProvider = Provider<GoRouter>((ref) {
  final refresco = ref.watch(_refrescoDelRouterProvider);

  return GoRouter(
    initialLocation: '/splash',
    refreshListenable: refresco,
    redirect: (context, state) {
      final authState = ref.read(authControllerProvider);
      final ruta = state.matchedLocation;
      final esAuth = _esRutaAuth(ruta);
      final esSplash = ruta == '/splash';

      switch (authState.estado) {
        case EstadoSesion.inicial:
          return esSplash ? null : '/splash';
        case EstadoSesion.cargando:
          // No redirigir mientras carga: login()/registrar() también ponen
          // este estado al tocar "Ingresar" desde /login, y si acá se
          // forzara volver a /splash, su initState llamaría restaurarSesion()
          // de nuevo en paralelo con el login en curso -- una carrera que
          // podía pisar el resultado real del login. Cada pantalla (splash,
          // login, registro) ya muestra su propio indicador de carga.
          return null;
        case EstadoSesion.noAutenticado:
          if (esSplash) return '/home';
          if (esAuth) return null;
          if (_esRutaPublicaParaInvitado(ruta)) return null;
          return '/login?returnTo=${Uri.encodeComponent(state.uri.toString())}';
        case EstadoSesion.autenticado:
          if (esSplash) return '/home';
          if (esAuth) {
            final returnTo = state.uri.queryParameters['returnTo'];
            return (returnTo != null && returnTo.isNotEmpty) ? returnTo : '/home';
          }
          return null;
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
      GoRoute(path: '/carrito', builder: (context, state) => const CarritoScreen()),
      GoRoute(path: '/checkout/entrega', builder: (context, state) => const EntregaScreen()),
      GoRoute(path: '/checkout/direccion/nueva', builder: (context, state) => const DireccionFormScreen()),
      GoRoute(path: '/checkout/pago', builder: (context, state) => const PagoScreen()),
      GoRoute(
        path: '/checkout/estado/:pagoId',
        builder: (context, state) => EstadoPagoScreen(pagoId: int.parse(state.pathParameters['pagoId']!)),
      ),
      GoRoute(path: '/compras', builder: (context, state) => const MisComprasScreen()),
      GoRoute(
        path: '/compras/:id',
        builder: (context, state) => CompraDetalleScreen(ventaId: int.parse(state.pathParameters['id']!)),
      ),
    ],
  );
});
