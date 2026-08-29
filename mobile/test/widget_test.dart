import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/core/network/providers.dart';
import 'package:mobile/main.dart';

import 'helpers/token_storage_falso.dart';

void main() {
  testWidgets('sin sesión guardada, la app termina en la pantalla de login', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [tokenStorageProvider.overrideWithValue(TokenStorageFalso())],
        child: const FashionStoreApp(),
      ),
    );

    // No hay token guardado, así que restaurarSesion() resuelve rápido a
    // "no autenticado" y el router redirige de /splash a /login. No se usa
    // pumpAndSettle porque el spinner del splash anima indefinidamente.
    for (var i = 0; i < 10; i++) {
      await tester.pump(const Duration(milliseconds: 50));
    }

    expect(find.text('Bienvenido/a'), findsOneWidget);
  });
}
