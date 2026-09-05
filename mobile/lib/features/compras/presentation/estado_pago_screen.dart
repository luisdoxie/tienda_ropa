import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:webview_flutter/webview_flutter.dart';
import '../../../core/theme/app_theme.dart';
import '../state/checkout_controller.dart';
import '../state/compras_providers.dart';
import '../state/estado_pago_controller.dart';

// Mismas URLs hardcodeadas que backend/app/pagos/pasarela.py -- no hace
// falta que resuelvan de verdad: el WebView intercepta la navegación
// ANTES de intentar cargarlas.
const _prefijoRetorno = 'https://fashionstore.example.com/pago/retorno';
const _prefijoCancelado = 'https://fashionstore.example.com/pago/cancelado';

class EstadoPagoScreen extends ConsumerStatefulWidget {
  const EstadoPagoScreen({required this.pagoId, super.key});

  final int pagoId;

  @override
  ConsumerState<EstadoPagoScreen> createState() => _EstadoPagoScreenState();
}

class _EstadoPagoScreenState extends ConsumerState<EstadoPagoScreen> {
  late final WebViewController _webViewController;
  bool _webviewCerrado = false;
  bool _reintentando = false;

  @override
  void initState() {
    super.initState();
    final urlRedireccion = ref.read(checkoutControllerProvider).pagoIniciado?.urlRedireccion;

    _webViewController = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setNavigationDelegate(
        NavigationDelegate(
          onNavigationRequest: (request) {
            if (request.url.startsWith(_prefijoRetorno) || request.url.startsWith(_prefijoCancelado)) {
              _cerrarWebView();
              return NavigationDecision.prevent;
            }
            return NavigationDecision.navigate;
          },
          // Libélula es un simulador de sandbox: su "checkout" no existe de
          // verdad, así que esta URL nunca carga. No es un error fatal --
          // se cierra el WebView y el polling de GET /pagos/{id}/estado
          // (que ya está corriendo desde que se abrió la pantalla) sigue
          // siendo la fuente de verdad.
          onWebResourceError: (_) => _cerrarWebView(),
        ),
      );
    if (urlRedireccion != null) {
      _webViewController.loadRequest(Uri.parse(urlRedireccion));
    } else {
      _webviewCerrado = true;
    }
  }

  void _cerrarWebView() {
    if (!mounted || _webviewCerrado) return;
    setState(() => _webviewCerrado = true);
    ref.read(estadoPagoControllerProvider(widget.pagoId).notifier).consultarAhora();
  }

  Future<void> _reintentar() async {
    final checkout = ref.read(checkoutControllerProvider);
    final venta = checkout.venta;
    final metodoPago = checkout.pagoIniciado?.pago.metodoPago;
    if (venta == null || metodoPago == null) return;

    setState(() => _reintentando = true);
    try {
      final pagoIniciado = await ref
          .read(pagosRepositoryProvider)
          .iniciar(ventaId: venta.id, metodoPago: metodoPago);
      ref.read(checkoutControllerProvider.notifier).confirmarPago(pagoIniciado);
      if (!mounted) return;
      context.pushReplacement('/checkout/estado/${pagoIniciado.pago.id}');
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('No se pudo reintentar el pago. Probá de nuevo.')));
    } finally {
      if (mounted) setState(() => _reintentando = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    // Se mira siempre, no solo cuando se cierra el WebView: el polling
    // tiene que arrancar desde que se abre la pantalla, en paralelo a la
    // pasarela, no depender de que el WebView llegue a cerrarse.
    final estado = ref.watch(estadoPagoControllerProvider(widget.pagoId));

    return Scaffold(
      backgroundColor: AppColors.fondo,
      appBar: AppBar(
        title: const Text('Pago'),
        actions: [
          if (!_webviewCerrado)
            TextButton(onPressed: _cerrarWebView, child: const Text('Ya completé el pago')),
        ],
      ),
      body: _webviewCerrado
          ? _PanelEstado(estado: estado, reintentando: _reintentando, onReintentar: _reintentar)
          : WebViewWidget(controller: _webViewController),
    );
  }
}

class _PanelEstado extends StatelessWidget {
  const _PanelEstado({required this.estado, required this.reintentando, required this.onReintentar});

  final EstadoPagoEstado estado;
  final bool reintentando;
  final VoidCallback onReintentar;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.xl),
        child: estado.pago.when(
          loading: () => const Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              CircularProgressIndicator(color: AppColors.acento),
              SizedBox(height: AppSpacing.md),
              Text('Consultando el estado del pago...'),
            ],
          ),
          error: (e, s) => _MensajeEstado(
            icono: Icons.error_outline,
            color: AppColors.error,
            titulo: 'No se pudo consultar el pago',
            subtitulo: 'Revisá tu conexión y volvé a intentar.',
            reintentando: reintentando,
            onReintentar: onReintentar,
          ),
          data: (pago) {
            if (pago.aprobado) {
              return Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.check_circle, color: AppColors.exito, size: 56),
                  const SizedBox(height: AppSpacing.md),
                  const Text('¡Pago aprobado!', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
                  const SizedBox(height: AppSpacing.lg),
                  ElevatedButton(
                    onPressed: () => context.go('/compras/${pago.ventaId}'),
                    child: const Text('Ver mi compra'),
                  ),
                ],
              );
            }
            if (pago.rechazado) {
              return _MensajeEstado(
                icono: Icons.cancel_outlined,
                color: AppColors.error,
                titulo: 'El pago fue rechazado',
                subtitulo: 'Podés intentar de nuevo con el mismo método u otro.',
                reintentando: reintentando,
                onReintentar: onReintentar,
              );
            }
            if (estado.agotado) {
              return Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.hourglass_top, color: AppColors.textoTenue, size: 48),
                  const SizedBox(height: AppSpacing.md),
                  const Text(
                    'Pago pendiente de confirmación',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: AppSpacing.xs),
                  const Text(
                    'Todavía no tenemos la confirmación de la pasarela. Podés reintentar el pago o revisar más tarde en "Mis compras".',
                    style: TextStyle(color: AppColors.textoTenue, fontSize: 13),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: AppSpacing.lg),
                  ElevatedButton(
                    onPressed: reintentando ? null : onReintentar,
                    child: reintentando
                        ? const SizedBox(
                            height: 20,
                            width: 20,
                            child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                          )
                        : const Text('Reintentar'),
                  ),
                  const SizedBox(height: AppSpacing.sm),
                  TextButton(onPressed: () => context.go('/compras'), child: const Text('Ver mis compras')),
                ],
              );
            }
            return const Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                CircularProgressIndicator(color: AppColors.acento),
                SizedBox(height: AppSpacing.md),
                Text('Esperando la confirmación de la pasarela...'),
              ],
            );
          },
        ),
      ),
    );
  }
}

class _MensajeEstado extends StatelessWidget {
  const _MensajeEstado({
    required this.icono,
    required this.color,
    required this.titulo,
    required this.subtitulo,
    required this.reintentando,
    required this.onReintentar,
  });

  final IconData icono;
  final Color color;
  final String titulo;
  final String subtitulo;
  final bool reintentando;
  final VoidCallback onReintentar;

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icono, color: color, size: 56),
        const SizedBox(height: AppSpacing.md),
        Text(titulo, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700), textAlign: TextAlign.center),
        const SizedBox(height: AppSpacing.xs),
        Text(subtitulo, style: const TextStyle(color: AppColors.textoTenue), textAlign: TextAlign.center),
        const SizedBox(height: AppSpacing.lg),
        ElevatedButton(
          onPressed: reintentando ? null : onReintentar,
          child: reintentando
              ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
              : const Text('Reintentar'),
        ),
      ],
    );
  }
}
