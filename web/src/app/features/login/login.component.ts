import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { PasswordModule } from 'primeng/password';
import { switchMap } from 'rxjs';
import { AuthService } from '../../core/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [ReactiveFormsModule, ButtonModule, InputTextModule, PasswordModule],
  templateUrl: './login.component.html',
  styleUrl: './login.component.scss',
})
export class LoginComponent {
  protected readonly cargando = signal(false);
  protected readonly errorLogin = signal<string | null>(null);

  private readonly fb = inject(FormBuilder);
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);

  protected readonly formulario = this.fb.nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required]],
  });

  enviar(): void {
    if (this.formulario.invalid) {
      this.formulario.markAllAsTouched();
      return;
    }

    this.cargando.set(true);
    this.errorLogin.set(null);
    const { email, password } = this.formulario.getRawValue();

    this.authService
      .login(email, password)
      .pipe(switchMap(() => this.authService.cargarUsuarioActual()))
      .subscribe({
        next: () => {
          this.cargando.set(false);
          this.router.navigate(['/dashboard']);
        },
        error: () => {
          this.cargando.set(false);
          this.errorLogin.set('Email o contraseña incorrectos.');
        },
      });
  }
}
