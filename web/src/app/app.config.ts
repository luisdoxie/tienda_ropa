import { provideHttpClient, withInterceptors } from '@angular/common/http';
import {
  ApplicationConfig,
  inject,
  provideAppInitializer,
  provideBrowserGlobalErrorListeners,
} from '@angular/core';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { provideRouter } from '@angular/router';
import { definePreset } from '@primeuix/themes';
import Aura from '@primeuix/themes/aura';
import { MessageService } from 'primeng/api';
import { providePrimeNG } from 'primeng/config';
import { of } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { routes } from './app.routes';
import { AuthService } from './core/auth.service';
import { authInterceptor } from './core/auth.interceptor';
import { errorInterceptor } from './core/error.interceptor';
import { environment } from '../environments/environment';

// El preset de PrimeNG trae su propio color "primario" (el verde por
// defecto de Aura) que no tiene nada que ver con --fs-acento -- sin esto,
// cada p-button/p-checkbox/etc. se queda con el verde de fábrica aunque el
// resto del CSS ya esté en terracota. Rampa 50-950 derivada del acento
// #9A3E1F (CLAUDE.md, tokens de diseño).
const FashionStorePreset = definePreset(Aura, {
  semantic: {
    primary: {
      50: '#f7ede7',
      100: '#ecd6c8',
      200: '#ddb69e',
      300: '#c99274',
      400: '#b06e4c',
      500: '#9a3e1f',
      600: '#732e16',
      700: '#5c2512',
      800: '#451c0e',
      900: '#2f1309',
      950: '#1c0b05',
    },
  },
});

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideRouter(routes),
    provideHttpClient(withInterceptors([errorInterceptor, authInterceptor])),
    provideAnimationsAsync(),
    providePrimeNG({
      theme: { preset: FashionStorePreset, options: { darkModeSelector: '.fs-oscuro' } },
      license: environment.primeuiLicense,
    }),
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
