import { HttpClient } from '@angular/common/http';
import { Component, ViewChild, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ButtonModule } from 'primeng/button';
import { DialogModule } from 'primeng/dialog';
import { InputTextModule } from 'primeng/inputtext';
import { environment } from '../../../environments/environment';
import { Rol } from '../../core/models/seguridad.models';
import { ColumnaTabla, TablaGenericaComponent } from '../../shared/tabla-generica/tabla-generica.component';

const COLUMNAS: ColumnaTabla<Rol>[] = [
  { campo: 'nombre', encabezado: 'Nombre' },
  { campo: 'descripcion', encabezado: 'Descripción' },
  { campo: 'activo', encabezado: 'Activo', tipo: 'booleano' },
];

@Component({
  selector: 'app-roles',
  standalone: true,
  imports: [ReactiveFormsModule, ButtonModule, DialogModule, InputTextModule, TablaGenericaComponent],
  templateUrl: './roles.component.html',
})
export class RolesComponent {
  protected readonly columnas = COLUMNAS;
  protected readonly dialogoVisible = signal(false);
  protected readonly editando = signal<Rol | null>(null);

  @ViewChild(TablaGenericaComponent) private tabla!: TablaGenericaComponent<Rol>;

  private readonly fb = inject(FormBuilder);
  private readonly http = inject(HttpClient);

  protected readonly formulario = this.fb.nonNullable.group({
    nombre: ['', Validators.required],
    descripcion: [''],
  });

  abrirCrear(): void {
    this.editando.set(null);
    this.formulario.reset({ nombre: '', descripcion: '' });
    this.dialogoVisible.set(true);
  }

  abrirEditar(rol: Rol): void {
    this.editando.set(rol);
    this.formulario.reset({ nombre: rol.nombre, descripcion: rol.descripcion ?? '' });
    this.dialogoVisible.set(true);
  }

  guardar(): void {
    if (this.formulario.invalid) {
      this.formulario.markAllAsTouched();
      return;
    }

    const datos = this.formulario.getRawValue();
    const rol = this.editando();
    const peticion = rol
      ? this.http.put(`${environment.apiUrl}/roles/${rol.id}`, datos)
      : this.http.post(`${environment.apiUrl}/roles`, datos);

    peticion.subscribe(() => {
      this.dialogoVisible.set(false);
      this.tabla.recargar();
    });
  }
}
