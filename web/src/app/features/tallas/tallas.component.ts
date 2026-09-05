import { HttpClient } from '@angular/common/http';
import { Component, ViewChild, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ButtonModule } from 'primeng/button';
import { DialogModule } from 'primeng/dialog';
import { InputNumberModule } from 'primeng/inputnumber';
import { InputTextModule } from 'primeng/inputtext';
import { environment } from '../../../environments/environment';
import { Talla, TallaCrear } from '../../core/models/catalogo.models';
import { ColumnaTabla, TablaGenericaComponent } from '../../shared/tabla-generica/tabla-generica.component';

const COLUMNAS: ColumnaTabla<Talla>[] = [
  { campo: 'codigo', encabezado: 'Código' },
  { campo: 'descripcion', encabezado: 'Descripción' },
  { campo: 'orden', encabezado: 'Orden' },
];

@Component({
  selector: 'app-tallas',
  standalone: true,
  imports: [ReactiveFormsModule, ButtonModule, DialogModule, InputNumberModule, InputTextModule, TablaGenericaComponent],
  templateUrl: './tallas.component.html',
})
export class TallasComponent {
  protected readonly columnas = COLUMNAS;
  protected readonly dialogoVisible = signal(false);
  protected readonly editando = signal<Talla | null>(null);

  @ViewChild(TablaGenericaComponent) private tabla!: TablaGenericaComponent<Talla>;

  private readonly fb = inject(FormBuilder);
  private readonly http = inject(HttpClient);

  protected readonly formulario = this.fb.nonNullable.group({
    codigo: ['', Validators.required],
    descripcion: [''],
    orden: [0],
  });

  abrirCrear(): void {
    this.editando.set(null);
    this.formulario.reset({ codigo: '', descripcion: '', orden: 0 });
    this.dialogoVisible.set(true);
  }

  abrirEditar(talla: Talla): void {
    this.editando.set(talla);
    this.formulario.reset({ codigo: talla.codigo, descripcion: talla.descripcion ?? '', orden: talla.orden });
    this.dialogoVisible.set(true);
  }

  guardar(): void {
    if (this.formulario.invalid) {
      this.formulario.markAllAsTouched();
      return;
    }

    const valores = this.formulario.getRawValue();
    const talla = this.editando();
    const datos: TallaCrear = { codigo: valores.codigo, descripcion: valores.descripcion || null, orden: valores.orden };

    const peticion = talla
      ? this.http.put(`${environment.apiUrl}/tallas/${talla.id}`, datos)
      : this.http.post(`${environment.apiUrl}/tallas`, datos);

    peticion.subscribe(() => {
      this.dialogoVisible.set(false);
      this.tabla.recargar();
    });
  }
}
