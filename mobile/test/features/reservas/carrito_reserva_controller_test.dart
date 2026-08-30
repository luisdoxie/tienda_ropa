import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/features/reservas/models/item_reserva_temporal.dart';
import 'package:mobile/features/reservas/state/carrito_reserva_controller.dart';

ItemReservaTemporal _item(int varianteId) => ItemReservaTemporal(
  varianteId: varianteId,
  productoNombre: 'Camisa',
  sku: 'SKU-$varianteId',
  tallaCodigo: 'M',
  colorNombre: 'Azul',
);

void main() {
  group('CarritoReservaController', () {
    test('arranca vacío', () {
      final controller = CarritoReservaController();
      expect(controller.state, isEmpty);
    });

    test('agregar suma un item nuevo', () {
      final controller = CarritoReservaController();
      controller.agregar(_item(1));
      expect(controller.state, hasLength(1));
      expect(controller.contiene(1), isTrue);
    });

    test('agregar la misma variante dos veces no la duplica', () {
      final controller = CarritoReservaController();
      controller.agregar(_item(1));
      controller.agregar(_item(1));
      expect(controller.state, hasLength(1));
    });

    test('quitar elimina solo esa variante', () {
      final controller = CarritoReservaController();
      controller.agregar(_item(1));
      controller.agregar(_item(2));
      controller.quitar(1);
      expect(controller.state, hasLength(1));
      expect(controller.contiene(1), isFalse);
      expect(controller.contiene(2), isTrue);
    });

    test('vaciar deja la lista vacía', () {
      final controller = CarritoReservaController();
      controller.agregar(_item(1));
      controller.agregar(_item(2));
      controller.vaciar();
      expect(controller.state, isEmpty);
    });
  });
}
