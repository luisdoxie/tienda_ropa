import { HttpClient } from '@angular/common/http';
import { Component, OnInit, ViewChild, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ButtonModule } from 'primeng/button';
import { DialogModule } from 'primeng/dialog';
import { InputNumberModule } from 'primeng/inputnumber';
import { InputTextModule } from 'primeng/inputtext';
import { SelectModule } from 'primeng/select';
import { environment } from '../../../environments/environment';
import { ZonaEnvio, ZonaEnvioCrear } from '../../core/models/entregas.models';
import { Ciudad } from '../../core/models/organizacion.models';
import { ColumnaTabla, TablaGenericaComponent } from '../../shared/tabla-generica/tabla-generica.component';

const COLUMNAS: ColumnaTabla<ZonaEnvio>[] = [
  { campo: 'nombre', encabezado: 'Nombre' },
  { campo: 'anillo_desde', encabezado: 'Anillo desde' },
  { campo: 'anillo_hasta', encabezado: 'Anillo hasta' },
  { campo: 'tarifa_base', encabezado: 'Tarifa base' },
  { campo: 'activo', encabezado: 'Activo', tipo: 'booleano' },
];

@Component({
  selector: 'app-zonas-envio',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    ButtonModule,
    DialogModule,
    InputNumberModule,
    InputTextModule,
    SelectModule,
    TablaGenericaComponent,
  ],
  templateUrl: './zonas-envio.component.html',
})
export class ZonasEnvioComponent implements OnInit {
  protected readonly columnas = COLUMNAS;
  protected readonly dialogoVisible = signal(false);
  protected readonly editando = signal<ZonaEnvio | null>(null);
  protected readonly ciudades = signal<Ciudad[]>([]);

  @ViewChild(TablaGenericaComponent) private tabla!: TablaGenericaComponent<ZonaEnvio>;

  private readonly fb = inject(FormBuilder);
  private readonly http = inject(HttpClient);

  protected readonly formulario = this.fb.nonNullable.group({
    ciudad_id: [null as number | null, Validators.required],
    nombre: ['', Validators.required],
    anillo_desde: [null as number | null],
    anillo_hasta: [null as number | null],
    tarifa_base: [0, [Validators.required, Validators.min(0)]],
  });

  ngOnInit(): void {
    this.http
      .get<Ciudad[]>(`${environment.apiUrl}/ciudades?pagina=1&tamanio=100`)
      .subscribe((ciudades) => this.ciudades.set(ciudades));
  }

  abrirCrear(): void {
    this.editando.set(null);
    this.formulario.reset({ ciudad_id: null, nombre: '', anillo_desde: null, anillo_hasta: null, tarifa_base: 0 });
    this.dialogoVisible.set(true);
  }

  abrirEditar(zona: ZonaEnvio): void {
    this.editando.set(zona);
    this.formulario.reset({
      ciudad_id: zona.ciudad_id,
      nombre: zona.nombre,
      anillo_desde: zona.anillo_desde,
      anillo_hasta: zona.anillo_hasta,
      tarifa_base: zona.tarifa_base,
    });
    this.dialogoVisible.set(true);
  }

  guardar(): void {
    if (this.formulario.invalid) {
      this.formulario.markAllAsTouched();
      return;
    }

    const valores = this.formulario.getRawValue();
    const zona = this.editando();

    const peticion = zona
      ? this.http.put(`${environment.apiUrl}/zonas-envio/${zona.id}`, {
          nombre: valores.nombre,
          anillo_desde: valores.anillo_desde,
          anillo_hasta: valores.anillo_hasta,
          tarifa_base: valores.tarifa_base,
        })
      : this.http.post<ZonaEnvioCrear>(`${environment.apiUrl}/zonas-envio`, {
          ciudad_id: valores.ciudad_id!,
          nombre: valores.nombre,
          anillo_desde: valores.anillo_desde,
          anillo_hasta: valores.anillo_hasta,
          tarifa_base: valores.tarifa_base,
        });

    peticion.subscribe(() => {
      this.dialogoVisible.set(false);
      this.tabla.recargar();
    });
  }
}
