import { Component, computed, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { AuthService } from '../../core/auth.service';

@Component({
  selector: 'app-solicitar-recuperacion',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, ButtonModule, InputTextModule],
  templateUrl: './solicitar-recuperacion.component.html',
})
export class SolicitarRecuperacionComponent {
  protected readonly cargando = signal(false);
  protected readonly enviado = signal(false);
  protected readonly enlaceDev = signal<string | null>(null);

  private readonly fb = inject(FormBuilder);
  private readonly authService = inject(AuthService);

  protected readonly formulario = this.fb.nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
  });

  protected readonly mostrarEnlaceDev = computed(() => this.enlaceDev() !== null);

  enviar(): void {
    if (this.formulario.invalid) {
      this.formulario.markAllAsTouched();
      return;
    }

    this.cargando.set(true);
    const { email } = this.formulario.getRawValue();

    this.authService.solicitarRecuperacion(email).subscribe({
      next: (respuesta) => {
        this.cargando.set(false);
        this.enviado.set(true);
        this.enlaceDev.set(
          respuesta.token_dev
            ? `${window.location.origin}/restablecer?token=${encodeURIComponent(respuesta.token_dev)}`
            : null,
        );
      },
      error: () => {
        // El backend responde genérico incluso para emails no registrados;
        // un error acá solo puede ser de red, así que se muestra igual el
        // mensaje de éxito para no revelar nada sobre el email.
        this.cargando.set(false);
        this.enviado.set(true);
      },
    });
  }
}
