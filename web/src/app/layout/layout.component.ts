import { Component, computed, inject } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { ButtonModule } from 'primeng/button';
import { AuthService } from '../core/auth.service';

interface ItemMenu {
  etiqueta: string;
  icono: string;
  ruta: string;
  permiso?: string;
}

const ITEMS_MENU: ItemMenu[] = [
  { etiqueta: 'Dashboard', icono: 'pi pi-home', ruta: '/dashboard' },
  { etiqueta: 'Usuarios', icono: 'pi pi-users', ruta: '/usuarios', permiso: 'usuarios.gestionar' },
  { etiqueta: 'Roles', icono: 'pi pi-shield', ruta: '/roles', permiso: 'roles.gestionar' },
  { etiqueta: 'Ciudades', icono: 'pi pi-map', ruta: '/ciudades', permiso: 'organizacion.gestionar' },
  {
    etiqueta: 'Sucursales',
    icono: 'pi pi-building',
    ruta: '/sucursales',
    permiso: 'organizacion.gestionar',
  },
];

@Component({
  selector: 'app-layout',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive, ButtonModule],
  templateUrl: './layout.component.html',
  styleUrl: './layout.component.scss',
})
export class LayoutComponent {
  private readonly authService = inject(AuthService);

  protected readonly usuario = this.authService.usuario;

  protected readonly itemsMenu = computed(() =>
    ITEMS_MENU.filter((item) => !item.permiso || this.authService.tienePermiso(item.permiso)),
  );

  cerrarSesion(): void {
    this.authService.logout();
  }
}
