import { HttpClient } from '@angular/common/http';
import { Component, ViewChild, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ButtonModule } from 'primeng/button';
import { CheckboxModule } from 'primeng/checkbox';
import { DialogModule } from 'primeng/dialog';
import { InputTextModule } from 'primeng/inputtext';
import { PasswordModule } from 'primeng/password';
import { environment } from '../../../environments/environment';
import { Usuario } from '../../core/models/seguridad.models';
import { ColumnaTabla, TablaGenericaComponent } from '../../shared/tabla-generica/tabla-generica.component';

const COLUMNAS: ColumnaTabla<Usuario>[] = [
  { campo: 'nombre', encabezado: 'Nombre' },
  { campo: 'apellido', encabezado: 'Apellido' },
  { campo: 'email', encabezado: 'Email' },
  { campo: 'activo', encabezado: 'Activo', tipo: 'booleano' },
];

@Component({
  selector: 'app-usuarios',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    ButtonModule,
    DialogModule,
    InputTextModule,
    PasswordModule,
    CheckboxModule,
    TablaGenericaComponent,
  ],
  templateUrl: './usuarios.component.html',
})
export class UsuariosComponent {
  protected readonly columnas = COLUMNAS;
  protected readonly dialogoVisible = signal(false);
  protected readonly editando = signal<Usuario | null>(null);

  @ViewChild(TablaGenericaComponent) private tabla!: TablaGenericaComponent<Usuario>;

  private readonly fb = inject(FormBuilder);
  private readonly http = inject(HttpClient);

  protected readonly formulario = this.fb.nonNullable.group({
    nombre: ['', Validators.required],
    apellido: ['', Validators.required],
    email: ['', [Validators.required, Validators.email]],
    telefono: [''],
    password: [''],
    activo: [true],
  });

  abrirCrear(): void {
    this.editando.set(null);
    this.formulario.reset({ nombre: '', apellido: '', email: '', telefono: '', password: '', activo: true });
    this.formulario.controls.email.enable();
    this.formulario.controls.password.setValidators([Validators.required, Validators.minLength(8)]);
    this.formulario.controls.password.updateValueAndValidity();
    this.dialogoVisible.set(true);
  }

  abrirEditar(usuario: Usuario): void {
    this.editando.set(usuario);
    this.formulario.reset({
      nombre: usuario.nombre,
      apellido: usuario.apellido,
      email: usuario.email,
      telefono: usuario.telefono ?? '',
      password: '',
      activo: usuario.activo,
    });
    this.formulario.controls.email.disable(); // el email no se edita, es la identidad de login
    this.formulario.controls.password.clearValidators();
    this.formulario.controls.password.updateValueAndValidity();
    this.dialogoVisible.set(true);
  }

  guardar(): void {
    if (this.formulario.invalid) {
      this.formulario.markAllAsTouched();
      return;
    }

    const usuario = this.editando();
    const peticion = usuario
      ? this.http.put(`${environment.apiUrl}/usuarios/${usuario.id}`, {
          nombre: this.formulario.controls.nombre.value,
          apellido: this.formulario.controls.apellido.value,
          telefono: this.formulario.controls.telefono.value,
          activo: this.formulario.controls.activo.value,
        })
      : this.http.post(`${environment.apiUrl}/usuarios`, {
          nombre: this.formulario.controls.nombre.value,
          apellido: this.formulario.controls.apellido.value,
          email: this.formulario.controls.email.value,
          telefono: this.formulario.controls.telefono.value,
          password: this.formulario.controls.password.value,
        });

    peticion.subscribe(() => {
      this.dialogoVisible.set(false);
      this.tabla.recargar();
    });
  }
}
