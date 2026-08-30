import 'dart:io';

import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:google_mlkit_pose_detection/google_mlkit_pose_detection.dart';
import 'package:permission_handler/permission_handler.dart';

import '../../../core/theme/app_theme.dart';

/// Paso previo al overlay del probador (ver P4.4): solo detección de pose.
/// Objetivo único: confirmar que los landmarks de hombros y caderas caen
/// donde corresponde y son estables frente a la cámara frontal, antes de
/// dibujar ninguna prenda encima.
class PoseDebugScreen extends StatefulWidget {
  const PoseDebugScreen({super.key});

  @override
  State<PoseDebugScreen> createState() => _PoseDebugScreenState();
}

enum _EstadoPermiso { pidiendo, concedido, denegado, denegadoPermanente }

class _PoseDebugScreenState extends State<PoseDebugScreen> with WidgetsBindingObserver {
  final _detectorPose = PoseDetector(options: PoseDetectorOptions(mode: PoseDetectionMode.stream));

  CameraController? _controller;
  CameraDescription? _camaraFrontal;
  _EstadoPermiso _estadoPermiso = _EstadoPermiso.pidiendo;
  bool _procesandoFrame = false;
  Pose? _ultimaPose;
  Size? _tamanioImagen;
  InputImageRotation _rotacion = InputImageRotation.rotation0deg;

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
    setState(() {
      _ultimaPose = poses.isNotEmpty ? poses.first : null;
      _tamanioImagen = inputImage.metadata!.size;
      _rotacion = inputImage.metadata!.rotation;
    });
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

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _controller?.dispose();
    _detectorPose.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: Colors.black,
        foregroundColor: Colors.white,
        title: const Text('Detección de pose'),
      ),
      body: _cuerpo(),
    );
  }

  Widget _cuerpo() {
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
            // El CustomPaint va como `child` de CameraPreview (no como
            // hermano en el Stack): así Flutter le da exactamente el mismo
            // tamaño que el recuadro del preview (limitado por AspectRatio),
            // que es el sistema de coordenadas que usan trasladarX/Y.
            Center(
              child: CameraPreview(
                controller,
                child: CustomPaint(
                  painter: _PosePainter(
                    pose: _ultimaPose,
                    tamanioImagen: _tamanioImagen,
                    rotacion: _rotacion,
                    direccionLente: _camaraFrontal?.lensDirection ?? CameraLensDirection.front,
                  ),
                ),
              ),
            ),
            _panelLikelihood(),
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

  Widget _panelLikelihood() {
    final pose = _ultimaPose;
    final hombroIzq = pose?.landmarks[PoseLandmarkType.leftShoulder];
    final hombroDer = pose?.landmarks[PoseLandmarkType.rightShoulder];
    return Positioned(
      left: AppSpacing.md,
      right: AppSpacing.md,
      bottom: AppSpacing.xl,
      child: Container(
        padding: const EdgeInsets.all(AppSpacing.md),
        decoration: BoxDecoration(color: Colors.black54, borderRadius: BorderRadius.circular(AppRadius.base)),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Text('Hombro izq.: ${_formatearLikelihood(hombroIzq?.likelihood)}', style: const TextStyle(color: Colors.white)),
            Text('Hombro der.: ${_formatearLikelihood(hombroDer?.likelihood)}', style: const TextStyle(color: Colors.white)),
          ],
        ),
      ),
    );
  }

  String _formatearLikelihood(double? valor) {
    if (valor == null) return 'sin detectar';
    return valor.toStringAsFixed(2);
  }
}

class _PosePainter extends CustomPainter {
  _PosePainter({required this.pose, required this.tamanioImagen, required this.rotacion, required this.direccionLente});

  final Pose? pose;
  final Size? tamanioImagen;
  final InputImageRotation rotacion;
  final CameraLensDirection direccionLente;

  static const _tiposAPintar = [
    PoseLandmarkType.leftShoulder,
    PoseLandmarkType.rightShoulder,
    PoseLandmarkType.leftHip,
    PoseLandmarkType.rightHip,
  ];

  @override
  void paint(Canvas canvas, Size size) {
    final pose = this.pose;
    final tamanioImagen = this.tamanioImagen;
    if (pose == null || tamanioImagen == null) return;

    final pincel = Paint()
      ..style = PaintingStyle.fill
      ..color = AppColors.exito;

    for (final tipo in _tiposAPintar) {
      final punto = pose.landmarks[tipo];
      if (punto == null) continue;
      final x = trasladarX(punto.x, size, tamanioImagen, rotacion, direccionLente);
      final y = trasladarY(punto.y, size, tamanioImagen, rotacion, direccionLente);
      canvas.drawCircle(Offset(x, y), 8, pincel);
    }
  }

  @override
  bool shouldRepaint(covariant _PosePainter oldDelegate) => oldDelegate.pose != pose;
}

// Traduce un punto de las coordenadas del buffer de la cámara (tal cual lo
// ve ML Kit) a coordenadas del canvas donde se dibuja. Para la cámara
// frontal el CameraPreview de Flutter ya renderiza el video espejado (como
// un espejo real), pero el buffer que procesa ML Kit NO está espejado —
// por eso acá se espeja también la coordenada X, para que el punto caiga
// sobre el hombro/cadera tal como se ve en pantalla y no al revés.
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
      return tamanioCanvas.width - x * tamanioCanvas.width / (Platform.isIOS ? tamanioImagen.width : tamanioImagen.height);
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
