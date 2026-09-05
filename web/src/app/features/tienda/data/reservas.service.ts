import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { HorarioSucursal } from '../../../core/models/organizacion.models';
import { Reserva, ReservaCrear } from '../../../core/models/reservas.models';

@Injectable({ providedIn: 'root' })
export class ReservasClienteService {
  private readonly http = inject(HttpClient);

  crear(datos: ReservaCrear): Observable<Reserva> {
    return this.http.post<Reserva>(`${environment.apiUrl}/reservas`, datos);
  }

  listarMisReservas(): Observable<Reserva[]> {
    return this.http.get<Reserva[]>(`${environment.apiUrl}/reservas/mis-reservas`);
  }

  obtener(reservaId: number): Observable<Reserva> {
    return this.http.get<Reserva>(`${environment.apiUrl}/reservas/${reservaId}`);
  }

  cancelar(reservaId: number): Observable<Reserva> {
    return this.http.delete<Reserva>(`${environment.apiUrl}/reservas/${reservaId}`);
  }

  horariosSucursal(sucursalId: number): Observable<HorarioSucursal[]> {
    return this.http.get<HorarioSucursal[]>(`${environment.apiUrl}/sucursales/${sucursalId}/horarios`);
  }
}
