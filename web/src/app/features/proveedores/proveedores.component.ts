import { HttpClient } from '@angular/common/http';
import { Component, ViewChild, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ButtonModule } from 'primeng/button';
import { DialogModule } from 'primeng/dialog';
import { InputTextModule } from 'primeng/inputtext';
import { environment } from '../../../environments/environment';
import { Proveedor, ProveedorCrear } from '../../core/models/abastecimiento.models';
import { ColumnaTabla, TablaGenericaComponent } from '../../shared/tabla-generica/tabla-generica.component';

const COLUMNAS: ColumnaTabla<Proveedor>[] = [
  { campo: 'nombre', encabezado: 'Nombre' },
  { campo: 'nit', encabezado: 'NIT' },
  { campo: 'contacto', encabezado: 'Contacto' },
  { campo: 'telefono', encabezado: 'Teléfono' },
  { campo: 'activo', encabezado: 'Activo', tipo: 'booleano' },
];

@Component({
  selector: 'app-proveedores',
  standalone: true,
  imports: [ReactiveFormsModule, ButtonModule, DialogModule, InputTextModule, TablaGenericaComponent],
  templateUrl: './proveedores.component.html',
})
export class ProveedoresComponent {
  protected readonly columnas = COLUMNAS;
  protected readonly dialogoVisible = signal(false);
  protected readonly editando = signal<Proveedor | null>(null);

  @ViewChild(TablaGenericaComponent) private tabla!: TablaGenericaComponent<Proveedor>;

  private readonly fb = inject(FormBuilder);
  private readonly http = inject(HttpClient);

  protected readonly formulario = this.fb.nonNullable.group({
    nombre: ['', Validators.required],
    nit: [''],
    contacto: [''],
    telefono: [''],
    email: ['', Validators.email],
    direccion: [''],
  });

  abrirCrear(): void {
    this.editando.set(null);
    this.formulario.reset({ nombre: '', nit: '', contacto: '', telefono: '', email: '', direccion: '' });
    this.dialogoVisible.set(true);
  }

  abrirEditar(proveedor: Proveedor): void {
    this.editando.set(proveedor);
    this.formulario.reset({
      nombre: proveedor.nombre,
      nit: proveedor.nit ?? '',
      contacto: proveedor.contacto ?? '',
      telefono: proveedor.telefono ?? '',
      email: proveedor.email ?? '',
      direccion: proveedor.direccion ?? '',
    });
    this.dialogoVisible.set(true);
  }

  guardar(): void {
    if (this.formulario.invalid) {
      this.formulario.markAllAsTouched();
      return;
    }

    const valores = this.formulario.getRawValue();
    const proveedor = this.editando();
    const datos: ProveedorCrear = {
      nombre: valores.nombre,
      nit: valores.nit || null,
      contacto: valores.contacto || null,
      telefono: valores.telefono || null,
      email: valores.email || null,
      direccion: valores.direccion || null,
    };

    const peticion = proveedor
      ? this.http.put(`${environment.apiUrl}/proveedores/${proveedor.id}`, datos)
      : this.http.post(`${environment.apiUrl}/proveedores`, datos);

    peticion.subscribe(() => {
      this.dialogoVisible.set(false);
      this.tabla.recargar();
    });
  }
}
