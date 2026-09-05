import { HttpClient } from '@angular/common/http';
import { Component, ViewChild, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ButtonModule } from 'primeng/button';
import { DialogModule } from 'primeng/dialog';
import { InputTextModule } from 'primeng/inputtext';
import { environment } from '../../../environments/environment';
import { Color, ColorCrear } from '../../core/models/catalogo.models';
import { ColumnaTabla, TablaGenericaComponent } from '../../shared/tabla-generica/tabla-generica.component';

const COLUMNAS: ColumnaTabla<Color>[] = [
  { campo: 'nombre', encabezado: 'Nombre' },
  { campo: 'codigo_hex', encabezado: 'Color (hex)' },
];

@Component({
  selector: 'app-colores',
  standalone: true,
  imports: [ReactiveFormsModule, ButtonModule, DialogModule, InputTextModule, TablaGenericaComponent],
  templateUrl: './colores.component.html',
})
export class ColoresComponent {
  protected readonly columnas = COLUMNAS;
  protected readonly dialogoVisible = signal(false);
  protected readonly editando = signal<Color | null>(null);

  @ViewChild(TablaGenericaComponent) private tabla!: TablaGenericaComponent<Color>;

  private readonly fb = inject(FormBuilder);
  private readonly http = inject(HttpClient);

  protected readonly formulario = this.fb.nonNullable.group({
    nombre: ['', Validators.required],
    codigo_hex: ['', Validators.pattern(/^#[0-9A-Fa-f]{6}$/)],
  });

  abrirCrear(): void {
    this.editando.set(null);
    this.formulario.reset({ nombre: '', codigo_hex: '' });
    this.dialogoVisible.set(true);
  }

  abrirEditar(color: Color): void {
    this.editando.set(color);
    this.formulario.reset({ nombre: color.nombre, codigo_hex: color.codigo_hex ?? '' });
    this.dialogoVisible.set(true);
  }

  guardar(): void {
    if (this.formulario.invalid) {
      this.formulario.markAllAsTouched();
      return;
    }

    const valores = this.formulario.getRawValue();
    const color = this.editando();
    const datos: ColorCrear = { nombre: valores.nombre, codigo_hex: valores.codigo_hex || null };

    const peticion = color
      ? this.http.put(`${environment.apiUrl}/colores/${color.id}`, datos)
      : this.http.post(`${environment.apiUrl}/colores`, datos);

    peticion.subscribe(() => {
      this.dialogoVisible.set(false);
      this.tabla.recargar();
    });
  }
}
