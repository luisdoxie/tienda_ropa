import { DecimalPipe } from '@angular/common';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { switchMap } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { ProductoImagenLookupItem } from '../../../core/models/catalogo.models';
import { Venta, VentaDetalle } from '../../../core/models/ventas.models';
import { PedidosService } from '../data/pedidos.service';

interface LineaComprobante extends VentaDetalle {
  productoNombre?: string;
  imagenPrincipal?: string | null;
  tallaCodigo?: string | null;
  colorNombre?: string | null;
}

@Component({
  selector: 'app-compra-detalle',
  standalone: true,
  imports: [RouterLink, DecimalPipe],
  templateUrl: './compra-detalle.component.html',
  styleUrl: './compra-detalle.component.scss',
})
export class CompraDetalleComponent implements OnInit {
  private readonly http = inject(HttpClient);
  private readonly route = inject(ActivatedRoute);
  private readonly pedidosService = inject(PedidosService);

  protected readonly venta = signal<Venta | null>(null);
  protected readonly lineas = signal<LineaComprobante[]>([]);
  protected readonly cargando = signal(true);
  protected readonly error = signal(false);

  ngOnInit(): void {
    const ventaId = Number(this.route.snapshot.paramMap.get('id'));
    this.pedidosService
      .obtenerComprobante(ventaId)
      .pipe(
        switchMap((venta) => {
          this.venta.set(venta);
          const params = new HttpParams().set('variante_ids', venta.detalle.map((d) => d.variante_id).join(','));
          return this.http.get<ProductoImagenLookupItem[]>(`${environment.apiUrl}/catalogo/variantes/detalle`, {
            params,
          });
        }),
      )
      .subscribe({
        next: (lookup) => {
          const porVariante = new Map(lookup.map((item) => [item.variante_id, item]));
          const detalle = this.venta()!.detalle;
          this.lineas.set(
            detalle.map((linea) => {
              const item = porVariante.get(linea.variante_id);
              return {
                ...linea,
                productoNombre: item?.producto_nombre,
                imagenPrincipal: item?.imagen_principal,
                tallaCodigo: item?.talla_codigo,
                colorNombre: item?.color_nombre,
              };
            }),
          );
          this.cargando.set(false);
        },
        error: () => {
          this.cargando.set(false);
          this.error.set(true);
        },
      });
  }
}
