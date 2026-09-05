import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { Venta, VentaDigitalCrear } from '../../../core/models/ventas.models';

@Injectable({ providedIn: 'root' })
export class PedidosService {
  private readonly http = inject(HttpClient);

  registrarVentaDigital(datos: VentaDigitalCrear): Observable<Venta> {
    return this.http.post<Venta>(`${environment.apiUrl}/ventas/digital`, datos);
  }

  listarMisCompras(): Observable<Venta[]> {
    return this.http.get<Venta[]>(`${environment.apiUrl}/ventas/mis-compras`);
  }

  obtenerComprobante(ventaId: number): Observable<Venta> {
    return this.http.get<Venta>(`${environment.apiUrl}/ventas/${ventaId}/comprobante`);
  }
}
