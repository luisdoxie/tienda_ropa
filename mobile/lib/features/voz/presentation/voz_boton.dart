import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:speech_to_text/speech_to_text.dart';

import '../../../core/theme/app_theme.dart';
import '../../catalogo/state/catalogo_controller.dart';
import '../state/voz_providers.dart';

/// Botón de micrófono del catálogo (P6.1): pide permiso, transcribe con el
/// reconocimiento nativo del dispositivo (`speech_to_text`, sin backend de
/// por medio para la transcripción) y manda el texto a POST /ia/voz. Los
/// resultados y filtros que devuelve el backend se aplican directo al
/// catálogo, sin volver a pedirlos (ver
/// CatalogoController.aplicarFiltrosDesdeVoz).
class VozBoton extends ConsumerWidget {
  const VozBoton({super.key});

  Future<void> _iniciar(BuildContext context, WidgetRef ref) async {
    final permiso = await Permission.microphone.request();
    if (!context.mounted) return;

    if (permiso.isPermanentlyDenied) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: const Text('El micrófono está bloqueado. Habilitalo desde los ajustes del sistema.'),
          action: SnackBarAction(label: 'Ajustes', onPressed: openAppSettings),
        ),
      );
      return;
    }
    if (!permiso.isGranted) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('Se necesita acceso al micrófono para buscar por voz.')));
      return;
    }

    final speech = SpeechToText();
    final disponible = await speech.initialize();
    if (!context.mounted) return;
    if (!disponible) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('Este dispositivo no tiene reconocimiento de voz disponible.')));
      return;
    }

    final texto = await showModalBottomSheet<String>(
      context: context,
      isDismissible: false,
      enableDrag: false,
      isScrollControlled: true,
      builder: (context) => _HojaEscucha(speech: speech),
    );
    await speech.stop();
    if (texto == null || texto.trim().isEmpty || !context.mounted) return;

    await _buscar(context, ref, texto);
  }

  Future<void> _buscar(BuildContext context, WidgetRef ref, String texto) async {
    showDialog<void>(
      context: context,
      barrierDismissible: false,
      builder: (context) => const Center(child: CircularProgressIndicator(color: AppColors.acento)),
    );
    try {
      final resultado = await ref.read(vozRepositoryProvider).buscarPorVoz(texto);
      if (!context.mounted) return;
      Navigator.of(context, rootNavigator: true).pop();
      ref
          .read(catalogoControllerProvider.notifier)
          .aplicarFiltrosDesdeVoz(resultado.filtros, resultado.resultados, resultado.etiquetas);
    } catch (_) {
      if (!context.mounted) return;
      Navigator.of(context, rootNavigator: true).pop();
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('No se pudo completar la búsqueda por voz.')));
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return IconButton.filledTonal(
      icon: const Icon(Icons.mic_none_outlined),
      tooltip: 'Buscar por voz',
      onPressed: () => _iniciar(context, ref),
    );
  }
}

/// Hoja modal que arranca a escuchar apenas se abre y se cierra sola con el
/// resultado final (o con lo que se llevaba transcrito, si el usuario la
/// cierra a mano con "Detener").
class _HojaEscucha extends StatefulWidget {
  const _HojaEscucha({required this.speech});

  final SpeechToText speech;

  @override
  State<_HojaEscucha> createState() => _HojaEscuchaState();
}

class _HojaEscuchaState extends State<_HojaEscucha> {
  String _textoParcial = '';
  double _nivelSonido = 0;

  @override
  void initState() {
    super.initState();
    _escuchar();
  }

  Future<void> _escuchar() async {
    final localeId = _elegirLocale(await widget.speech.locales());
    await widget.speech.listen(
      listenOptions: SpeechListenOptions(localeId: localeId, partialResults: true, cancelOnError: true),
      onSoundLevelChange: (nivel) {
        if (!mounted) return;
        setState(() => _nivelSonido = nivel);
      },
      onResult: (resultado) {
        if (!mounted) return;
        setState(() => _textoParcial = resultado.recognizedWords);
        if (resultado.finalResult) {
          Navigator.of(context).pop(resultado.recognizedWords);
        }
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    // El rango real de onSoundLevelChange difiere entre Android e iOS (ver
    // el doc del propio paquete); clamp + normalizado a 0..1 alcanza para
    // un pulso visual, no hace falta un valor exacto en decibeles.
    final escala = 1 + (_nivelSonido.clamp(0, 10) / 10) * 0.3;
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.lg),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            AnimatedScale(
              scale: escala,
              duration: const Duration(milliseconds: 100),
              child: const CircleAvatar(
                radius: 36,
                backgroundColor: AppColors.acento,
                child: Icon(Icons.mic, color: Colors.white, size: 32),
              ),
            ),
            const SizedBox(height: AppSpacing.md),
            Text(
              _textoParcial.isEmpty ? 'Escuchando...' : _textoParcial,
              textAlign: TextAlign.center,
              style: const TextStyle(fontSize: 16),
            ),
            const SizedBox(height: AppSpacing.md),
            TextButton(
              onPressed: () => Navigator.of(context).pop(_textoParcial.isEmpty ? null : _textoParcial),
              child: const Text('Detener'),
            ),
          ],
        ),
      ),
    );
  }
}

String? _elegirLocale(List<LocaleName> locales) {
  String normalizar(String id) => id.toLowerCase().replaceAll('-', '_');
  for (final locale in locales) {
    if (normalizar(locale.localeId) == 'es_bo') return locale.localeId;
  }
  for (final locale in locales) {
    if (normalizar(locale.localeId) == 'es_es') return locale.localeId;
  }
  for (final locale in locales) {
    if (normalizar(locale.localeId).startsWith('es')) return locale.localeId;
  }
  return null;
}
