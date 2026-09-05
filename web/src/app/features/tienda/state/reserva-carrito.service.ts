import { Injectable, computed, signal } from '@angular/core';

export interface ItemReservaTemporal {
  varianteId: number;
  productoNombre: string;
  tallaCodigo: string;
  colorNombre: string;
  imagenPrincipal: string | null;
}

/**
 * Carrito de "quiero probarme esto en tienda", efímero -- se pierde al
 * recargar la página, igual que `carrito_reserva_controller.dart` en
 * Flutter (mismo criterio: es distinto del carrito de compra, que sí
 * persiste en el backend).
 */
@Injectable({ providedIn: 'root' })
export class ReservaCarritoService {
  private readonly items = signal<ItemReservaTemporal[]>([]);

  readonly lista = this.items.asReadonly();
  readonly cantidad = computed(() => this.items().length);

  contiene(varianteId: number): boolean {
    return this.items().some((item) => item.varianteId === varianteId);
  }

  agregar(item: ItemReservaTemporal): void {
    if (this.contiene(item.varianteId)) return;
    this.items.update((actual) => [...actual, item]);
  }

  quitar(varianteId: number): void {
    this.items.update((actual) => actual.filter((item) => item.varianteId !== varianteId));
  }

  vaciar(): void {
    this.items.set([]);
  }
}
