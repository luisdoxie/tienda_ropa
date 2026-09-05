import { Component, OnDestroy, OnInit, computed, inject } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { ButtonModule } from 'primeng/button';
import { PopoverModule } from 'primeng/popover';
import { AuthService } from '../core/auth.service';
import { NotificacionesService } from '../core/notificaciones.service';

const INTERVALO_NOTIFICACIONES_MS = 20_000;

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
  { etiqueta: 'Probador', icono: 'pi pi-camera', ruta: '/probador', permiso: 'probador.gestionar' },
  { etiqueta: 'Inventario', icono: 'pi pi-box', ruta: '/inventario', permiso: 'inventario.ver' },
  { etiqueta: 'Productos', icono: 'pi pi-tag', ruta: '/productos', permiso: 'catalogo.gestionar' },
  { etiqueta: 'Categorías', icono: 'pi pi-sitemap', ruta: '/categorias', permiso: 'catalogo.gestionar' },
  { etiqueta: 'Tallas', icono: 'pi pi-tags', ruta: '/tallas', permiso: 'catalogo.gestionar' },
  { etiqueta: 'Colores', icono: 'pi pi-palette', ruta: '/colores', permiso: 'catalogo.gestionar' },
  { etiqueta: 'Temporadas', icono: 'pi pi-sun', ruta: '/temporadas', permiso: 'catalogo.gestionar' },
  { etiqueta: 'Colecciones', icono: 'pi pi-images', ruta: '/colecciones', permiso: 'catalogo.gestionar' },
  {
    etiqueta: 'Proveedores',
    icono: 'pi pi-truck',
    ruta: '/proveedores',
    permiso: 'abastecimiento.gestionar',
  },
  {
    etiqueta: 'Reservas',
    icono: 'pi pi-calendar-clock',
    ruta: '/reservas',
    permiso: 'reservas.gestionar_sucursal',
  },
  { etiqueta: 'Caja', icono: 'pi pi-shopping-cart', ruta: '/caja', permiso: 'ventas.presencial' },
  { etiqueta: 'Promociones', icono: 'pi pi-percentage', ruta: '/promociones', permiso: 'ventas.gestionar' },
  { etiqueta: 'Zonas de envío', icono: 'pi pi-truck', ruta: '/zonas-envio', permiso: 'entregas.gestionar' },
];

@Component({
  selector: 'app-layout',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive, ButtonModule, PopoverModule],
  templateUrl: './layout.component.html',
  styleUrl: './layout.component.scss',
})
export class LayoutComponent implements OnInit, OnDestroy {
  private readonly authService = inject(AuthService);
  protected readonly notificacionesService = inject(NotificacionesService);

  protected readonly usuario = this.authService.usuario;

  protected readonly itemsMenu = computed(() =>
    ITEMS_MENU.filter((item) => !item.permiso || this.authService.tienePermiso(item.permiso)),
  );

  private intervalo?: ReturnType<typeof setInterval>;

  ngOnInit(): void {
    this.notificacionesService.cargar().subscribe();
    // ~20s: "casi en tiempo real" sin WebSockets, mismo mecanismo de
    // polling que ya usa checkout-estado.component.ts para el pago.
    this.intervalo = setInterval(() => this.notificacionesService.cargar().subscribe(), INTERVALO_NOTIFICACIONES_MS);
  }

  ngOnDestroy(): void {
    clearInterval(this.intervalo);
  }

  marcarLeida(notificacionId: number): void {
    this.notificacionesService.marcarLeida(notificacionId).subscribe();
  }

  cerrarSesion(): void {
    this.authService.logout();
  }
}
