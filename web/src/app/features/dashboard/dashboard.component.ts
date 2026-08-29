import { Component, inject } from '@angular/core';
import { AuthService } from '../../core/auth.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  template: `
    <h1>Dashboard</h1>
    <p>Bienvenido/a, {{ usuario()?.nombre }}. Los indicadores se agregan en la etapa 6.</p>
  `,
})
export class DashboardComponent {
  private readonly authService = inject(AuthService);
  protected readonly usuario = this.authService.usuario;
}
