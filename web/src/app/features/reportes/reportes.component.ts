import { DatePipe, DecimalPipe } from '@angular/common';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ButtonModule } from 'primeng/button';
import { ChartModule } from 'primeng/chart';
import { DatePickerModule } from 'primeng/datepicker';
import { SelectModule } from 'primeng/select';
import { TableModule } from 'primeng/table';
import { TabsModule } from 'primeng/tabs';
import { environment } from '../../../environments/environment';
import { fechaLocalIso } from '../../core/date-utils';
import { Categoria } from '../../core/models/catalogo.models';
import { Empleado, Sucursal } from '../../core/models/organizacion.models';
import { DashboardReportes, ReporteInventario, ReporteReservas, ReporteVentas } from '../../core/models/reportes.models';

type PestaniaReportes = 'dashboard' | 'ventas' | 'inventario' | 'reservas';

const OPCIONES_CANAL = [
  { label: 'Todos los canales', value: null },
  { label: 'Digital', value: 'digital' },
  { label: 'Presencial', value: 'presencial' },
];

@Component({
  selector: 'app-reportes',
  standalone: true,
  imports: [
    DatePipe,
    DecimalPipe,
    FormsModule,
    ButtonModule,
    ChartModule,
    DatePickerModule,
    SelectModule,
    TableModule,
    TabsModule,
  ],
  templateUrl: './reportes.component.html',
  styleUrl: './reportes.component.scss',
})
export class ReportesComponent implements OnInit {
  private readonly http = inject(HttpClient);

  protected readonly opcionesCanal = OPCIONES_CANAL;

  protected readonly pestania = signal<PestaniaReportes>('dashboard');

  // ---- Filtros compartidos ----------------------------------------------------------

  protected readonly sucursales = signal<Sucursal[]>([]);
  protected readonly categorias = signal<Categoria[]>([]);
  protected readonly filtroSucursalId = signal<number | null>(null);
  // Un encargado_sucursal está atado a su sucursal (resuelta vía
  // /empleados/yo, mismo criterio que dashboard.component.ts): el filtro
  // queda fijo, no elige "todas". Un administrador sin registro de
  // empleado sí puede elegir cualquiera o ninguna.
  protected readonly sucursalBloqueada = signal(false);
  protected readonly filtroCategoriaId = signal<number | null>(null);
  protected readonly filtroCanal = signal<string | null>(null);
  protected readonly filtroDesde = signal<Date | null>(null);
  protected readonly filtroHasta = signal<Date | null>(null);

  // ---- Datos por pestaña --------------------------------------------------------------

  protected readonly dashboard = signal<DashboardReportes | null>(null);
  protected readonly cargandoDashboard = signal(false);

  protected readonly ventas = signal<ReporteVentas | null>(null);
  protected readonly cargandoVentas = signal(false);

  protected readonly inventario = signal<ReporteInventario | null>(null);
  protected readonly cargandoInventario = signal(false);

  protected readonly reservas = signal<ReporteReservas | null>(null);
  protected readonly cargandoReservas = signal(false);

  // ---- Gráficos (p-chart) --------------------------------------------------------------

  protected readonly chartVentasPorCanal = computed(() => {
    const filas = this.dashboard()?.ventas_por_canal ?? this.ventas()?.por_canal ?? [];
    return {
      labels: filas.map((f) => (f.canal === 'digital' ? 'Digital' : 'Presencial')),
      datasets: [{ data: filas.map((f) => Number(f.total_ventas)), backgroundColor: ['#9A3E1F', '#C9BCB2'] }],
    };
  });

  protected readonly chartVentasPorSucursal = computed(() => {
    const filas = this.ventas()?.por_sucursal ?? this.dashboard()?.ventas_por_sucursal ?? [];
    return {
      labels: filas.map((f) => f.sucursal),
      datasets: [{ label: 'Ventas', data: filas.map((f) => Number(f.total_ventas)), backgroundColor: '#9A3E1F' }],
    };
  });

  protected readonly chartTopProductos = computed(() => {
    const filas = this.ventas()?.top_productos ?? this.dashboard()?.top_productos ?? [];
    return {
      labels: filas.map((f) => f.producto),
      datasets: [
        { label: 'Cantidad vendida', data: filas.map((f) => f.cantidad_vendida), backgroundColor: '#9A3E1F' },
      ],
    };
  });

  protected readonly chartReservasPorEstado = computed(() => {
    const filas = this.reservas()?.por_estado ?? this.dashboard()?.reservas_por_estado ?? [];
    return {
      labels: filas.map((f) => f.nombre),
      datasets: [
        {
          data: filas.map((f) => f.cantidad),
          backgroundColor: ['#9A3E1F', '#B45309', '#16A34A', '#C7BCAC', '#DC2626'],
        },
      ],
    };
  });

  ngOnInit(): void {
    this.http
      .get<Sucursal[]>(`${environment.apiUrl}/sucursales?pagina=1&tamanio=100`)
      .subscribe((sucursales) => this.sucursales.set(sucursales));
    this.http
      .get<Categoria[]>(`${environment.apiUrl}/categorias?pagina=1&tamanio=100`)
      .subscribe((categorias) => this.categorias.set(categorias));

    this.http.get<Empleado>(`${environment.apiUrl}/empleados/yo`).subscribe({
      next: (empleado) => {
        if (empleado.sucursal_id !== null) {
          this.filtroSucursalId.set(empleado.sucursal_id);
          this.sucursalBloqueada.set(true);
        }
        this.buscarDashboard();
      },
      // Sin registro de empleado (típico de un administrador puro): queda
      // libre para elegir cualquier sucursal, o ninguna (vista global).
      error: () => this.buscarDashboard(),
    });
  }

  cambiarPestania(valor: string): void {
    const pestania = valor as PestaniaReportes;
    this.pestania.set(pestania);
    this.buscarPestaniaActual();
  }

  aplicarFiltros(): void {
    this.buscarPestaniaActual();
  }

  private buscarPestaniaActual(): void {
    switch (this.pestania()) {
      case 'dashboard':
        this.buscarDashboard();
        break;
      case 'ventas':
        this.buscarVentas();
        break;
      case 'inventario':
        this.buscarInventario();
        break;
      case 'reservas':
        this.buscarReservas();
        break;
    }
  }

  private parametrosPeriodo(): HttpParams {
    let params = new HttpParams();
    if (this.filtroSucursalId() !== null) params = params.set('sucursal_id', this.filtroSucursalId()!);
    if (this.filtroDesde() !== null) params = params.set('desde', fechaLocalIso(this.filtroDesde()!));
    if (this.filtroHasta() !== null) params = params.set('hasta', fechaLocalIso(this.filtroHasta()!));
    return params;
  }

  buscarDashboard(): void {
    this.cargandoDashboard.set(true);
    this.http.get<DashboardReportes>(`${environment.apiUrl}/reportes/dashboard`, { params: this.parametrosPeriodo() }).subscribe({
      next: (datos) => {
        this.dashboard.set(datos);
        this.cargandoDashboard.set(false);
      },
      error: () => this.cargandoDashboard.set(false),
    });
  }

  buscarVentas(): void {
    this.cargandoVentas.set(true);
    let params = this.parametrosPeriodo();
    if (this.filtroCategoriaId() !== null) params = params.set('categoria_id', this.filtroCategoriaId()!);
    if (this.filtroCanal() !== null) params = params.set('canal', this.filtroCanal()!);
    this.http.get<ReporteVentas>(`${environment.apiUrl}/reportes/ventas`, { params }).subscribe({
      next: (datos) => {
        this.ventas.set(datos);
        this.cargandoVentas.set(false);
      },
      error: () => this.cargandoVentas.set(false),
    });
  }

  buscarInventario(): void {
    this.cargandoInventario.set(true);
    let params = new HttpParams();
    if (this.filtroSucursalId() !== null) params = params.set('sucursal_id', this.filtroSucursalId()!);
    this.http.get<ReporteInventario>(`${environment.apiUrl}/reportes/inventario`, { params }).subscribe({
      next: (datos) => {
        this.inventario.set(datos);
        this.cargandoInventario.set(false);
      },
      error: () => this.cargandoInventario.set(false),
    });
  }

  buscarReservas(): void {
    this.cargandoReservas.set(true);
    this.http.get<ReporteReservas>(`${environment.apiUrl}/reportes/reservas`, { params: this.parametrosPeriodo() }).subscribe({
      next: (datos) => {
        this.reservas.set(datos);
        this.cargandoReservas.set(false);
      },
      error: () => this.cargandoReservas.set(false),
    });
  }
}
