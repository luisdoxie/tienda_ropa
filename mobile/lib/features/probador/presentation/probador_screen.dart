import 'dart:async';
import 'dart:io';
import 'dart:ui' as ui;

import 'package:cached_network_image/cached_network_image.dart';
import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gal/gal.dart';
import 'package:google_mlkit_pose_detection/google_mlkit_pose_detection.dart';
import 'package:permission_handler/permission_handler.dart';

import '../../../core/theme/app_theme.dart';
import '../models/activo_probador.dart';
import '../state/probador_providers.dart';

/// Probador virtual en modo espejo: cámara frontal + ML Kit (detección de
/// pose, ver P4.4) + overlay de la prenda encima, siguiendo hombros y
/// caderas en tiempo real (P4.5).
class ProbadorScreen extends ConsumerStatefulWidget {
  const ProbadorScreen({super.key});

  @override
  ConsumerState<ProbadorScreen> createState() => _ProbadorScreenState();
}

enum _EstadoPermiso { pidiendo, concedido, denegado, denegadoPermanente }

class _ProbadorScreenState extends ConsumerState<ProbadorScreen> with WidgetsBindingObserver {
  final _detectorPose = PoseDetector(options: PoseDetectorOptions(mode: PoseDetectionMode.stream));
  final _repaintKey = GlobalKey();

  static const _umbralLikelihood = 0.6;
  static const _factorSuavizado = 0.3;

  CameraController? _controller;
  CameraDescription? _camaraFrontal;
  _EstadoPermiso _estadoPermiso = _EstadoPermiso.pidiendo;
  bool _procesandoFrame = false;

  Size? _tamanioImagenCamara;
  InputImageRotation _rotacion = InputImageRotation.rotation0deg;
  bool _poseValida = false;
  // Coordenadas suavizadas de los hombros, en el sistema de coordenadas
  // del buffer de la cámara (antes de trasladarX/Y): la suavización va acá
  // porque ese sistema no cambia de tamaño entre frames, a diferencia del
  // canvas donde se pinta.
  Offset? _hombroIzqSuavizado;
  Offset? _hombroDerSuavizado;

  PrendaProbador? _prendaActual;
  ui.Image? _imagenPrenda;
  bool _cargandoImagen = false;
  bool _sesionRegistrada = false;
  bool _capturando = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _pedirPermisoYArrancar();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState estado) {
    final controller = _controller;
    if (controller == null || !controller.value.isInitialized) return;
    if (estado == AppLifecycleState.inactive || estado == AppLifecycleState.paused) {
      controller.dispose();
      _controller = null;
    } else if (estado == AppLifecycleState.resumed) {
      _iniciarCamara();
    }
  }

  Future<void> _pedirPermisoYArrancar() async {
    final resultado = await Permission.camera.request();
    if (!mounted) return;
    if (resultado.isGranted) {
      setState(() => _estadoPermiso = _EstadoPermiso.concedido);
      await _iniciarCamara();
    } else if (resultado.isPermanentlyDenied) {
      setState(() => _estadoPermiso = _EstadoPermiso.denegadoPermanente);
    } else {
      setState(() => _estadoPermiso = _EstadoPermiso.denegado);
    }
  }

  Future<void> _iniciarCamara() async {
    final camaras = await availableCameras();
    if (camaras.isEmpty) return;
    final camaraFrontal = camaras.firstWhere(
      (c) => c.lensDirection == CameraLensDirection.front,
      orElse: () => camaras.first,
    );
    _camaraFrontal = camaraFrontal;

    final controller = CameraController(
      camaraFrontal,
      ResolutionPreset.medium,
      enableAudio: false,
      imageFormatGroup: Platform.isAndroid ? ImageFormatGroup.nv21 : ImageFormatGroup.bgra8888,
    );
    _controller = controller;
    await controller.initialize();
    if (!mounted) return;
    await controller.startImageStream(_procesarFrame);
    setState(() {});
  }

  void _procesarFrame(CameraImage imagen) {
    if (_procesandoFrame) return;
    _procesandoFrame = true;
    _detectar(imagen).whenComplete(() => _procesandoFrame = false);
  }

  Future<void> _detectar(CameraImage imagen) async {
    final inputImage = _construirInputImage(imagen);
    if (inputImage == null || inputImage.metadata == null) return;
    final poses = await _detectorPose.processImage(inputImage);
    if (!mounted) return;

    final pose = poses.isNotEmpty ? poses.first : null;
    final hombroIzq = pose?.landmarks[PoseLandmarkType.leftShoulder];
    final hombroDer = pose?.landmarks[PoseLandmarkType.rightShoulder];
    final valido =
        hombroIzq != null &&
        hombroDer != null &&
        hombroIzq.likelihood >= _umbralLikelihood &&
        hombroDer.likelihood >= _umbralLikelihood;

    setState(() {
      _tamanioImagenCamara = inputImage.metadata!.size;
      _rotacion = inputImage.metadata!.rotation;
      _poseValida = valido;
      if (valido) {
        _hombroIzqSuavizado = _suavizar(_hombroIzqSuavizado, Offset(hombroIzq.x, hombroIzq.y));
        _hombroDerSuavizado = _suavizar(_hombroDerSuavizado, Offset(hombroDer.x, hombroDer.y));
      } else {
        // Se reinicia (no se congela) para que, cuando vuelva a detectarse
        // una pose válida, no arranque suavizando desde una posición vieja.
        _hombroIzqSuavizado = null;
        _hombroDerSuavizado = null;
      }
    });
  }

  Offset _suavizar(Offset? anterior, Offset nuevo) {
    if (anterior == null) return nuevo;
    return Offset.lerp(anterior, nuevo, _factorSuavizado)!;
  }

  // Rotación real del sensor según orientación del dispositivo: la cámara
  // frontal en Android suma la compensación (en vez de restarla como la
  // trasera) porque su sensor está montado espejado respecto de la trasera.
  static const _orientaciones = {
    DeviceOrientation.portraitUp: 0,
    DeviceOrientation.landscapeLeft: 90,
    DeviceOrientation.portraitDown: 180,
    DeviceOrientation.landscapeRight: 270,
  };

  InputImage? _construirInputImage(CameraImage imagen) {
    final controller = _controller;
    final camara = _camaraFrontal;
    if (controller == null || camara == null) return null;

    InputImageRotation? rotacion;
    if (Platform.isIOS) {
      rotacion = InputImageRotationValue.fromRawValue(camara.sensorOrientation);
    } else if (Platform.isAndroid) {
      var compensacion = _orientaciones[controller.value.deviceOrientation];
      if (compensacion == null) return null;
      if (camara.lensDirection == CameraLensDirection.front) {
        compensacion = (camara.sensorOrientation + compensacion) % 360;
      } else {
        compensacion = (camara.sensorOrientation - compensacion + 360) % 360;
      }
      rotacion = InputImageRotationValue.fromRawValue(compensacion);
    }
    if (rotacion == null) return null;

    final formato = InputImageFormatValue.fromRawValue(imagen.format.raw);
    if (formato == null ||
        (Platform.isAndroid && formato != InputImageFormat.nv21) ||
        (Platform.isIOS && formato != InputImageFormat.bgra8888)) {
      return null;
    }

    // Con imageFormatGroup nv21/bgra8888 la cámara ya entrega un solo plano.
    if (imagen.planes.length != 1) return null;
    final plano = imagen.planes.first;

    return InputImage.fromBytes(
      bytes: plano.bytes,
      metadata: InputImageMetadata(
        size: Size(imagen.width.toDouble(), imagen.height.toDouble()),
        rotation: rotacion,
        format: formato,
        bytesPerRow: plano.bytesPerRow,
      ),
    );
  }

  Future<void> _elegirPrenda(PrendaProbador prenda, {bool esInicial = false}) async {
    if (_cargandoImagen) return;
    setState(() => _cargandoImagen = true);
    try {
      final bytes = await ref.read(probadorRepositoryProvider).obtenerImagenOverlay(prenda.assets.overlay);
      final codec = await ui.instantiateImageCodec(bytes);
      final frame = await codec.getNextFrame();
      if (!mounted) return;
      setState(() {
        _prendaActual = prenda;
        _imagenPrenda = frame.image;
        _cargandoImagen = false;
      });
      if (esInicial && !_sesionRegistrada) {
        _sesionRegistrada = true;
        unawaited(ref.read(probadorRepositoryProvider).registrarSesion(varianteId: prenda.varianteId, modo: 'espejo'));
      }
    } catch (e, stack) {
      debugPrint('Error cargando overlay de la prenda ${prenda.varianteId}: $e\n$stack');
      if (!mounted) return;
      setState(() => _cargandoImagen = false);
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('No se pudo cargar la prenda.')));
    }
  }

  Future<void> _capturar() async {
    if (_capturando) return;
    setState(() => _capturando = true);
    try {
      final boundary = _repaintKey.currentContext?.findRenderObject() as RenderRepaintBoundary?;
      if (boundary == null) return;
      final imagen = await boundary.toImage(pixelRatio: 2.0);
      final bytes = await imagen.toByteData(format: ui.ImageByteFormat.png);
      if (bytes == null) return;

      final tienePermiso = await Gal.requestAccess();
      if (!tienePermiso) {
        if (!mounted) return;
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(const SnackBar(content: Text('Sin permiso para guardar en la galería.')));
        return;
      }
      await Gal.putImageBytes(bytes.buffer.asUint8List());
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Foto guardada en la galería.')));
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('No se pudo guardar la foto.')));
    } finally {
      if (mounted) setState(() => _capturando = false);
    }
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _controller?.dispose();
    _detectorPose.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    ref.listen<AsyncValue<List<PrendaProbador>>>(prendasProbadorProvider, (previous, next) {
      next.whenData((prendas) {
        if (prendas.isNotEmpty && _prendaActual == null) {
          _elegirPrenda(prendas.first, esInicial: true);
        }
      });
    });
    final asyncPrendas = ref.watch(prendasProbadorProvider);

    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(backgroundColor: Colors.black, foregroundColor: Colors.white, title: const Text('Probador')),
      body: _cuerpo(asyncPrendas),
    );
  }

  Widget _cuerpo(AsyncValue<List<PrendaProbador>> asyncPrendas) {
    switch (_estadoPermiso) {
      case _EstadoPermiso.pidiendo:
        return const Center(child: CircularProgressIndicator(color: Colors.white));
      case _EstadoPermiso.denegado:
        return _mensajePermiso(
          'Se necesita acceso a la cámara para el probador virtual.',
          textoBoton: 'Reintentar',
          onPressed: _pedirPermisoYArrancar,
        );
      case _EstadoPermiso.denegadoPermanente:
        return _mensajePermiso(
          'El acceso a la cámara está bloqueado. Habilitalo desde los ajustes del sistema.',
          textoBoton: 'Abrir ajustes',
          onPressed: openAppSettings,
        );
      case _EstadoPermiso.concedido:
        final controller = _controller;
        if (controller == null || !controller.value.isInitialized) {
          return const Center(child: CircularProgressIndicator(color: Colors.white));
        }
        return Stack(
          fit: StackFit.expand,
          children: [
            // Todo lo que tiene que quedar en la foto capturada (cámara +
            // prenda) va dentro de este RepaintBoundary; los controles de UI
            // (mensaje, selector, botón) van afuera, como hermanos en el Stack.
            RepaintBoundary(
              key: _repaintKey,
              child: Center(
                child: CameraPreview(
                  controller,
                  child: CustomPaint(
                    painter: _OverlayPainter(
                      imagenPrenda: _imagenPrenda,
                      activo: _prendaActual?.assets.overlay,
                      hombroIzqImg: _poseValida ? _hombroIzqSuavizado : null,
                      hombroDerImg: _poseValida ? _hombroDerSuavizado : null,
                      tamanioImagen: _tamanioImagenCamara,
                      rotacion: _rotacion,
                      direccionLente: _camaraFrontal?.lensDirection ?? CameraLensDirection.front,
                    ),
                  ),
                ),
              ),
            ),
            if (!_poseValida) _mensajeAcercate(),
            asyncPrendas.when(
              data: (prendas) => prendas.isEmpty ? _mensajeSinPrendas() : _selectorPrendas(prendas),
              loading: () => const SizedBox.shrink(),
              error: (error, stack) => const SizedBox.shrink(),
            ),
            _botonCaptura(),
          ],
        );
    }
  }

  Widget _mensajePermiso(String mensaje, {required String textoBoton, required VoidCallback onPressed}) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.lg),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.no_photography_outlined, color: Colors.white54, size: 48),
            const SizedBox(height: AppSpacing.md),
            Text(mensaje, style: const TextStyle(color: Colors.white), textAlign: TextAlign.center),
            const SizedBox(height: AppSpacing.md),
            ElevatedButton(onPressed: onPressed, child: Text(textoBoton)),
          ],
        ),
      ),
    );
  }

  Widget _mensajeAcercate() {
    return Positioned(
      top: AppSpacing.xl,
      left: AppSpacing.md,
      right: AppSpacing.md,
      child: Container(
        padding: const EdgeInsets.all(AppSpacing.sm),
        decoration: BoxDecoration(color: Colors.black54, borderRadius: BorderRadius.circular(AppRadius.base)),
        child: const Text('Acércate a la cámara', textAlign: TextAlign.center, style: TextStyle(color: Colors.white)),
      ),
    );
  }

  Widget _mensajeSinPrendas() {
    return Positioned(
      left: AppSpacing.md,
      right: AppSpacing.md,
      bottom: AppSpacing.xxl + 64,
      child: Container(
        padding: const EdgeInsets.all(AppSpacing.sm),
        decoration: BoxDecoration(color: Colors.black54, borderRadius: BorderRadius.circular(AppRadius.base)),
        child: const Text(
          'Todavía no hay prendas listas para probar.',
          textAlign: TextAlign.center,
          style: TextStyle(color: Colors.white),
        ),
      ),
    );
  }

  Widget _selectorPrendas(List<PrendaProbador> prendas) {
    return Positioned(
      left: 0,
      right: 0,
      bottom: AppSpacing.xxl + 64,
      child: SizedBox(
        height: 72,
        child: ListView.separated(
          scrollDirection: Axis.horizontal,
          padding: const EdgeInsets.symmetric(horizontal: AppSpacing.md),
          itemCount: prendas.length,
          separatorBuilder: (context, index) => const SizedBox(width: AppSpacing.sm),
          itemBuilder: (context, index) {
            final prenda = prendas[index];
            final seleccionada = prenda.varianteId == _prendaActual?.varianteId;
            return GestureDetector(
              onTap: () => _elegirPrenda(prenda),
              child: Container(
                width: 64,
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(AppRadius.base),
                  border: Border.all(
                    color: seleccionada ? AppColors.exito : Colors.white54,
                    width: seleccionada ? 3 : 1,
                  ),
                ),
                clipBehavior: Clip.antiAlias,
                child: CachedNetworkImage(
                  imageUrl: prenda.assets.overlay.url,
                  fit: BoxFit.cover,
                  placeholder: (context, url) => Container(color: Colors.white24),
                ),
              ),
            );
          },
        ),
      ),
    );
  }

  Widget _botonCaptura() {
    return Positioned(
      left: 0,
      right: 0,
      bottom: AppSpacing.xl,
      child: Center(
        child: FloatingActionButton(
          backgroundColor: AppColors.acento,
          onPressed: _capturar,
          child: _capturando
              ? const SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                )
              : const Icon(Icons.camera_alt, color: Colors.white),
        ),
      ),
    );
  }
}

class _OverlayPainter extends CustomPainter {
  _OverlayPainter({
    required this.imagenPrenda,
    required this.activo,
    required this.hombroIzqImg,
    required this.hombroDerImg,
    required this.tamanioImagen,
    required this.rotacion,
    required this.direccionLente,
  });

  final ui.Image? imagenPrenda;
  final ActivoProbador? activo;
  final Offset? hombroIzqImg;
  final Offset? hombroDerImg;
  final Size? tamanioImagen;
  final InputImageRotation rotacion;
  final CameraLensDirection direccionLente;

  // Factor de ajuste entre el ancho detectado de hombros y el ancho total
  // del asset (no el ancho entre sus propios anclajes): valor a ojo, se
  // afina mirando cómo queda puesta la prenda con overlays reales.
  static const _factorAncho = 2.6;

  @override
  void paint(Canvas canvas, Size size) {
    final imagen = imagenPrenda;
    final anclajes = activo?.anclajes;
    final anchoAssetPx = activo?.anchoPx;
    final altoAssetPx = activo?.altoPx;
    final izqImg = hombroIzqImg;
    final derImg = hombroDerImg;
    final tamanioImg = tamanioImagen;

    if (imagen == null ||
        anclajes == null ||
        anchoAssetPx == null ||
        altoAssetPx == null ||
        anchoAssetPx <= 0 ||
        altoAssetPx <= 0 ||
        izqImg == null ||
        derImg == null ||
        tamanioImg == null) {
      return;
    }

    final pIzq = Offset(
      trasladarX(izqImg.dx, size, tamanioImg, rotacion, direccionLente),
      trasladarY(izqImg.dy, size, tamanioImg, rotacion, direccionLente),
    );
    final pDer = Offset(
      trasladarX(derImg.dx, size, tamanioImg, rotacion, direccionLente),
      trasladarY(derImg.dy, size, tamanioImg, rotacion, direccionLente),
    );

    final transform = calcularTransformOverlay(
      pIzq: pIzq,
      pDer: pDer,
      anclajes: anclajes,
      anchoAssetPx: anchoAssetPx.toDouble(),
      altoAssetPx: altoAssetPx.toDouble(),
      factorAncho: _factorAncho,
    );
    if (transform == null) return;

    canvas.save();
    canvas.translate(transform.centro.dx, transform.centro.dy);
    canvas.rotate(transform.angulo);
    canvas.scale(transform.escala);
    // El punto medio de los anclajes del asset (no el origen de la imagen)
    // es lo que tiene que caer exactamente en `centro`: sin esta traslación
    // negativa, la prenda gira/escala alrededor de su esquina superior
    // izquierda y termina corrida en vez de centrada en el cuerpo.
    canvas.translate(-transform.anclaMedioPx.dx, -transform.anclaMedioPx.dy);
    canvas.drawImage(imagen, Offset.zero, Paint()..filterQuality = FilterQuality.high);
    canvas.restore();
  }

  @override
  bool shouldRepaint(covariant _OverlayPainter oldDelegate) {
    return oldDelegate.imagenPrenda != imagenPrenda ||
        oldDelegate.hombroIzqImg != hombroIzqImg ||
        oldDelegate.hombroDerImg != hombroDerImg;
  }
}

/// Los cuatro números que hacen falta para ubicar el overlay: dónde va
/// (`centro`), cuánto rota, cuánto escala y qué punto del asset es el que
/// tiene que terminar exactamente en `centro` (`anclaMedioPx`).
class TransformOverlay {
  const TransformOverlay({required this.centro, required this.angulo, required this.escala, required this.anclaMedioPx});

  final Offset centro;
  final double angulo;
  final double escala;
  final Offset anclaMedioPx;
}

/// El paso 6 del overlay, aislado de `Canvas` para poder testearlo: dados
/// los hombros ya detectados (en coordenadas de canvas) y los anclajes del
/// asset (fracciones 0..1 de su propio tamaño en píxeles), calcula la
/// transformación completa. Devuelve `null` si no hay con qué calcular
/// nada razonable (asset sin tamaño, o los dos hombros en el mismo punto).
TransformOverlay? calcularTransformOverlay({
  required Offset pIzq,
  required Offset pDer,
  required AnclajesProbador anclajes,
  required double anchoAssetPx,
  required double altoAssetPx,
  required double factorAncho,
}) {
  if (anchoAssetPx <= 0 || altoAssetPx <= 0) return null;

  final vector = pDer - pIzq;
  final ancho = vector.distance;
  if (ancho <= 0) return null;
  final angulo = vector.direction;
  final centro = Offset.lerp(pIzq, pDer, 0.5)!;

  final anclaIzqPx = Offset(anclajes.hombroIzq.x * anchoAssetPx, anclajes.hombroIzq.y * altoAssetPx);
  final anclaDerPx = Offset(anclajes.hombroDer.x * anchoAssetPx, anclajes.hombroDer.y * altoAssetPx);
  final anclaMedioPx = Offset.lerp(anclaIzqPx, anclaDerPx, 0.5)!;

  final escala = (ancho / anchoAssetPx) * factorAncho;

  return TransformOverlay(centro: centro, angulo: angulo, escala: escala, anclaMedioPx: anclaMedioPx);
}

// Traduce un punto de las coordenadas del buffer de la cámara (tal cual lo
// ve ML Kit) a coordenadas del canvas donde se dibuja. Para la cámara
// frontal el CameraPreview de Flutter ya renderiza el video espejado (como
// un espejo real), pero el buffer que procesa ML Kit NO está espejado —
// por eso acá se espeja también la coordenada X, para que el punto (y la
// prenda que se ancla en él) caigan tal como se ven en pantalla.
double trasladarX(
  double x,
  Size tamanioCanvas,
  Size tamanioImagen,
  InputImageRotation rotacion,
  CameraLensDirection direccionLente,
) {
  switch (rotacion) {
    case InputImageRotation.rotation90deg:
      return x * tamanioCanvas.width / (Platform.isIOS ? tamanioImagen.width : tamanioImagen.height);
    case InputImageRotation.rotation270deg:
      return tamanioCanvas.width -
          x * tamanioCanvas.width / (Platform.isIOS ? tamanioImagen.width : tamanioImagen.height);
    case InputImageRotation.rotation0deg:
    case InputImageRotation.rotation180deg:
      switch (direccionLente) {
        case CameraLensDirection.back:
          return x * tamanioCanvas.width / tamanioImagen.width;
        default:
          return tamanioCanvas.width - x * tamanioCanvas.width / tamanioImagen.width;
      }
  }
}

double trasladarY(
  double y,
  Size tamanioCanvas,
  Size tamanioImagen,
  InputImageRotation rotacion,
  CameraLensDirection direccionLente,
) {
  switch (rotacion) {
    case InputImageRotation.rotation90deg:
    case InputImageRotation.rotation270deg:
      return y * tamanioCanvas.height / (Platform.isIOS ? tamanioImagen.height : tamanioImagen.width);
    case InputImageRotation.rotation0deg:
    case InputImageRotation.rotation180deg:
      return y * tamanioCanvas.height / tamanioImagen.height;
  }
}
