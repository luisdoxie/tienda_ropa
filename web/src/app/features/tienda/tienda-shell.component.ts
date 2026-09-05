import { Component, effect, inject } from '@angular/core';
import { RouterLink, RouterOutlet } from '@angular/router';
import { AuthService } from '../../core/auth.service';
import { CarritoService } from './data/carrito.service';
import { ReservaCarritoService } from './state/reserva-carrito.service';

@Component({
  selector: 'app-tienda-shell',
  standalone: true,
  imports: [RouterLink, RouterOutlet],
  templateUrl: './tienda-shell.component.html',
  styleUrl: './tienda-shell.component.scss',
})
export class TiendaShellComponent {
  protected readonly authService = inject(AuthService);
  protected readonly carritoService = inject(CarritoService);
  protected readonly reservaCarritoService = inject(ReservaCarritoService);

  constructor() {
    effect(() => {
      if (this.authService.estaAutenticado()) {
        this.carritoService.cargar().subscribe({ error: () => undefined });
      } else {
        this.carritoService.limpiar();
      }
    });
  }

  cerrarSesion(): void {
    this.authService.logout();
  }
}
