import { provideHttpClient, withInterceptors } from '@angular/common/http';
import {
  ApplicationConfig,
  inject,
  provideAppInitializer,
  provideBrowserGlobalErrorListeners,
} from '@angular/core';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { provideRouter } from '@angular/router';
import Aura from '@primeuix/themes/aura';
import { MessageService } from 'primeng/api';
import { providePrimeNG } from 'primeng/config';
import { of } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { routes } from './app.routes';
import { AuthService } from './core/auth.service';
import { authInterceptor } from './core/auth.interceptor';
import { errorInterceptor } from './core/error.interceptor';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideRouter(routes),
    provideHttpClient(withInterceptors([errorInterceptor, authInterceptor])),
    provideAnimationsAsync(),
    providePrimeNG({ theme: { preset: Aura, options: { darkModeSelector: '.fs-oscuro' } } }),
    MessageService,
    // Restaura la sesión (si hay tokens guardados) antes de renderizar,
    // para que las guardas de ruta ya tengan roles/permisos disponibles.
    provideAppInitializer(() => {
      const authService = inject(AuthService);
      const restauracion = authService.restaurarSesion();
      if (!restauracion) {
        return of(null);
      }
      return restauracion.pipe(catchError(() => of(null)));
    }),
  ],
};
