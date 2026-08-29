import { HttpClient } from '@angular/common/http';
import { Component, OnInit, ViewChild, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ButtonModule } from 'primeng/button';
import { CheckboxModule } from 'primeng/checkbox';
import { DialogModule } from 'primeng/dialog';
import { InputTextModule } from 'primeng/inputtext';
import { SelectModule } from 'primeng/select';
import { environment } from '../../../environments/environment';
import { Ciudad } from '../../core/models/organizacion.models';
import { Sucursal } from '../../core/models/organizacion.models';
import { ColumnaTabla, TablaGenericaComponent } from '../../shared/tabla-generica/tabla-generica.component';

const COLUMNAS: ColumnaTabla<Sucursal>[] = [
  { campo: 'codigo', encabezado: 'Código' },
  { campo: 'nombre', encabezado: 'Nombre' },
  { campo: 'direccion', encabezado: 'Dirección' },
  { campo: 'activo', encabezado: 'Activo', tipo: 'booleano' },
];

@Component({
  selector: 'app-sucursales',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    ButtonModule,
    DialogModule,
    InputTextModule,
    CheckboxModule,
    SelectModule,
    TablaGenericaComponent,
  ],
  templateUrl: './sucursales.component.html',
})
export class SucursalesComponent implements OnInit {
  protected readonly columnas = COLUMNAS;
  protected readonly dialogoVisible = signal(false);
  protected readonly editando = signal<Sucursal | null>(null);
  protected readonly ciudades = signal<Ciudad[]>([]);

  @ViewChild(TablaGenericaComponent) private tabla!: TablaGenericaComponent<Sucursal>;

  private readonly fb = inject(FormBuilder);
  private readonly http = inject(HttpClient);

  protected readonly formulario = this.fb.nonNullable.group({
    ciudad_id: [null as number | null, Validators.required],
    codigo: ['', Validators.required],
    nombre: ['', Validators.required],
    direccion: ['', Validators.required],
    telefono: [''],
    es_deposito: [false],
    activo: [true],
  });

  ngOnInit(): void {
    // Todas las ciudades activas caben cómodas en una sola página para un
    // combo; si el catálogo crece, esto se cambia por un select con búsqueda
    // server-side.
    this.http
      .get<Ciudad[]>(`${environment.apiUrl}/ciudades?pagina=1&tamanio=100`)
      .subscribe((ciudades) => this.ciudades.set(ciudades));
  }

  abrirCrear(): void {
    this.editando.set(null);
    this.formulario.reset({
      ciudad_id: null,
      codigo: '',
      nombre: '',
      direccion: '',
      telefono: '',
      es_deposito: false,
      activo: true,
    });
    this.dialogoVisible.set(true);
  }

  abrirEditar(sucursal: Sucursal): void {
    this.editando.set(sucursal);
    this.formulario.reset({
      ciudad_id: sucursal.ciudad_id,
      codigo: sucursal.codigo,
      nombre: sucursal.nombre,
      direccion: sucursal.direccion,
      telefono: sucursal.telefono ?? '',
      es_deposito: sucursal.es_deposito,
      activo: sucursal.activo,
    });
    this.dialogoVisible.set(true);
  }

  guardar(): void {
    if (this.formulario.invalid) {
      this.formulario.markAllAsTouched();
      return;
    }

    const datos = this.formulario.getRawValue();
    const sucursal = this.editando();
    const peticion = sucursal
      ? this.http.put(`${environment.apiUrl}/sucursales/${sucursal.id}`, datos)
      : this.http.post(`${environment.apiUrl}/sucursales`, datos);

    peticion.subscribe(() => {
      this.dialogoVisible.set(false);
      this.tabla.recargar();
    });
  }
}
