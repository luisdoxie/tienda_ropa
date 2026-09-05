import { HttpClient } from '@angular/common/http';
import { Component, OnInit, ViewChild, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ButtonModule } from 'primeng/button';
import { DialogModule } from 'primeng/dialog';
import { InputTextModule } from 'primeng/inputtext';
import { SelectModule } from 'primeng/select';
import { environment } from '../../../environments/environment';
import { Coleccion, ColeccionCrear, Temporada } from '../../core/models/catalogo.models';
import { ColumnaTabla, TablaGenericaComponent } from '../../shared/tabla-generica/tabla-generica.component';

const COLUMNAS: ColumnaTabla<Coleccion>[] = [
  { campo: 'nombre', encabezado: 'Nombre' },
  { campo: 'descripcion', encabezado: 'Descripción' },
  { campo: 'activo', encabezado: 'Activo', tipo: 'booleano' },
];

@Component({
  selector: 'app-colecciones',
  standalone: true,
  imports: [ReactiveFormsModule, ButtonModule, DialogModule, InputTextModule, SelectModule, TablaGenericaComponent],
  templateUrl: './colecciones.component.html',
})
export class ColeccionesComponent implements OnInit {
  protected readonly columnas = COLUMNAS;
  protected readonly dialogoVisible = signal(false);
  protected readonly editando = signal<Coleccion | null>(null);
  protected readonly temporadas = signal<Temporada[]>([]);

  @ViewChild(TablaGenericaComponent) private tabla!: TablaGenericaComponent<Coleccion>;

  private readonly fb = inject(FormBuilder);
  private readonly http = inject(HttpClient);

  protected readonly formulario = this.fb.nonNullable.group({
    temporada_id: [null as number | null],
    nombre: ['', Validators.required],
    descripcion: [''],
  });

  ngOnInit(): void {
    this.http
      .get<Temporada[]>(`${environment.apiUrl}/temporadas?pagina=1&tamanio=100`)
      .subscribe((temporadas) => this.temporadas.set(temporadas));
  }

  abrirCrear(): void {
    this.editando.set(null);
    this.formulario.reset({ temporada_id: null, nombre: '', descripcion: '' });
    this.dialogoVisible.set(true);
  }

  abrirEditar(coleccion: Coleccion): void {
    this.editando.set(coleccion);
    this.formulario.reset({
      temporada_id: coleccion.temporada_id,
      nombre: coleccion.nombre,
      descripcion: coleccion.descripcion ?? '',
    });
    this.dialogoVisible.set(true);
  }

  guardar(): void {
    if (this.formulario.invalid) {
      this.formulario.markAllAsTouched();
      return;
    }

    const valores = this.formulario.getRawValue();
    const coleccion = this.editando();
    const datos: ColeccionCrear = {
      temporada_id: valores.temporada_id,
      nombre: valores.nombre,
      descripcion: valores.descripcion || null,
    };

    const peticion = coleccion
      ? this.http.put(`${environment.apiUrl}/colecciones/${coleccion.id}`, datos)
      : this.http.post(`${environment.apiUrl}/colecciones`, datos);

    peticion.subscribe(() => {
      this.dialogoVisible.set(false);
      this.tabla.recargar();
    });
  }
}
