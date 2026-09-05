import { Component, OnDestroy, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { MetodoPagoPasarela, Pago } from '../../../core/models/pagos.models';
import { PagosService } from '../data/pagos.service';
import { CheckoutService } from '../state/checkout.service';

const INTERVALO_MS = 3000;
const MAX_INTENTOS = 20;

@Component({
  selector: 'app-checkout-estado',
  standalone: true,
  imports: [RouterLink],
  templateUrl: './checkout-estado.component.html',
  styleUrl: './checkout-estado.component.scss',
})
export class CheckoutEstadoComponent implements OnInit, OnDestroy {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly pagosService = inject(PagosService);
  protected readonly checkoutService = inject(CheckoutService);

  protected readonly pagoId = signal(Number(this.route.snapshot.paramMap.get('pagoId')));
  protected readonly pago = signal<Pago | null>(null);
  protected readonly cargando = signal(true);
  protected readonly agotado = signal(false);
  protected readonly reintentando = signal(false);

  private intervalo?: ReturnType<typeof setInterval>;
  private intentos = 0;

  ngOnInit(): void {
    this.iniciarPolling();
  }

  ngOnDestroy(): void {
    clearInterval(this.intervalo);
  }

  consultarAhora(): void {
    this.cargando.set(true);
    this.consultar();
  }

  reintentar(): void {
    const venta = this.checkoutService.venta();
    const metodoPago = this.checkoutService.pagoIniciado()?.pago.metodo_pago as MetodoPagoPasarela | undefined;
    if (!venta || !metodoPago || this.reintentando()) return;

    this.reintentando.set(true);
    const ventana = window.open('', '_blank');
    ventana?.document.write('Redirigiendo a la pasarela de pago...');

    this.pagosService.iniciar(venta.id, metodoPago).subscribe({
      next: (pagoIniciado) => {
        this.checkoutService.confirmarPago(pagoIniciado);
        this.checkoutService.ventanaPago = ventana;
        if (ventana) {
          ventana.location.href = pagoIniciado.url_redireccion;
        }
        this.reintentando.set(false);
        this.pagoId.set(pagoIniciado.pago.id);
        this.intentos = 0;
        this.agotado.set(false);
        this.pago.set(null);
        this.iniciarPolling();
      },
      error: () => {
        ventana?.close();
        this.reintentando.set(false);
      },
    });
  }

  private iniciarPolling(): void {
    clearInterval(this.intervalo);
    this.consultarAhora();
    this.intervalo = setInterval(() => this.consultar(), INTERVALO_MS);
  }

  private consultar(): void {
    this.pagosService.obtenerEstado(this.pagoId()).subscribe({
      next: (pago) => {
        this.cargando.set(false);
        this.pago.set(pago);
        if (pago.estado === 'aprobado' || pago.estado === 'rechazado') {
          this.detener();
          return;
        }
        this.intentos += 1;
        if (this.intentos >= MAX_INTENTOS) {
          this.agotado.set(true);
          this.detener();
        }
      },
      error: () => this.cargando.set(false),
    });
  }

  private detener(): void {
    clearInterval(this.intervalo);
    this.checkoutService.ventanaPago?.close();
    this.checkoutService.ventanaPago = null;
  }

  irAMiCompra(): void {
    const ventaId = this.pago()?.venta_id;
    if (ventaId) {
      this.router.navigate(['/mis-compras', ventaId]);
    }
  }
}
