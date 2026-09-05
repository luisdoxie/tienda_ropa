import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { Observable, tap } from 'rxjs';
import { environment } from '../../environments/environment';
import { Notificacion } from './models/notificaciones.models';

/**
 * Estado de notificaciones con signals. No arranca el polling por su
 * cuenta -- lo controla `LayoutComponent` (ngOnInit/ngOnDestroy), para que
 * se detenga solo si el usuario navega fuera del back office o cierra
 * sesión, en vez de seguir pegándole a la API en segundo plano para
 * siempre (este servicio es `providedIn: 'root'`, vive toda la sesión).
 */
@Injectable({ providedIn: 'root' })
export class NotificacionesService {
  private readonly http = inject(HttpClient);
  private readonly lista = signal<Notificacion[]>([]);

  readonly notificaciones = this.lista.asReadonly();
  readonly noLeidas = computed(() => this.lista().filter((n) => !n.leida).length);

  cargar(): Observable<Notificacion[]> {
    return this.http
      .get<Notificacion[]>(`${environment.apiUrl}/notificaciones`)
      .pipe(tap((notificaciones) => this.lista.set(notificaciones)));
  }

  marcarLeida(notificacionId: number): Observable<Notificacion> {
    return this.http
      .put<Notificacion>(`${environment.apiUrl}/notificaciones/${notificacionId}/leida`, {})
      .pipe(
        tap((actualizada) => {
          this.lista.update((actual) => actual.map((n) => (n.id === actualizada.id ? actualizada : n)));
        }),
      );
  }
}
