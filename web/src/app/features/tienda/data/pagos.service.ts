import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { MetodoPagoPasarela, Pago, PagoIniciarRespuesta } from '../../../core/models/pagos.models';

@Injectable({ providedIn: 'root' })
export class PagosService {
  private readonly http = inject(HttpClient);

  iniciar(ventaId: number, metodoPago: MetodoPagoPasarela): Observable<PagoIniciarRespuesta> {
    return this.http.post<PagoIniciarRespuesta>(`${environment.apiUrl}/pagos/iniciar`, {
      venta_id: ventaId,
      metodo_pago: metodoPago,
    });
  }

  obtenerEstado(pagoId: number): Observable<Pago> {
    return this.http.get<Pago>(`${environment.apiUrl}/pagos/${pagoId}/estado`);
  }
}
