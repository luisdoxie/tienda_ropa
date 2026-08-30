import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/features/probador/presentation/probador_screen.dart';

void main() {
  group('debeAbandonarPolling', () {
    test('sigue reintentando si hay pocos fallos seguidos y poco tiempo transcurrido', () {
      expect(
        debeAbandonarPolling(intentosFallidosSeguidos: 1, transcurridoDesdeElInicio: const Duration(seconds: 4)),
        isFalse,
      );
    });

    test('abandona al llegar al máximo de intentos fallidos seguidos (corte de red)', () {
      expect(
        debeAbandonarPolling(intentosFallidosSeguidos: 5, transcurridoDesdeElInicio: const Duration(seconds: 10)),
        isTrue,
      );
      // Uno menos: todavía no abandona.
      expect(
        debeAbandonarPolling(intentosFallidosSeguidos: 4, transcurridoDesdeElInicio: const Duration(seconds: 8)),
        isFalse,
      );
    });

    test('abandona por tiempo total aunque no haya habido ningún fallo (servicio externo colgado)', () {
      expect(
        debeAbandonarPolling(intentosFallidosSeguidos: 0, transcurridoDesdeElInicio: const Duration(seconds: 91)),
        isTrue,
      );
      expect(
        debeAbandonarPolling(intentosFallidosSeguidos: 0, transcurridoDesdeElInicio: const Duration(seconds: 89)),
        isFalse,
      );
    });

    test('los umbrales son configurables', () {
      expect(
        debeAbandonarPolling(
          intentosFallidosSeguidos: 2,
          transcurridoDesdeElInicio: const Duration(seconds: 5),
          maxIntentosFallidosSeguidos: 2,
        ),
        isTrue,
      );
      expect(
        debeAbandonarPolling(
          intentosFallidosSeguidos: 0,
          transcurridoDesdeElInicio: const Duration(seconds: 5),
          timeoutTotal: const Duration(seconds: 3),
        ),
        isTrue,
      );
    });
  });
}
