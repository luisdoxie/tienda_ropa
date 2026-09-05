import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, switchMap, throwError } from 'rxjs';
import { environment } from '../../environments/environment';
import { AuthService } from './auth.service';

// '/catalogo' cubre /api/v1/catalogo, /catalogo/buscar, /catalogo/{id} y
// /catalogo/variantes/detalle -- es el único prefijo de router exclusivo
// del catálogo público (verificado: ningún endpoint de administración usa
// ese mismo prefijo). Sin esto, un 401 accidental ahí dispararía
// refrescarTokens()/logout() y mandaría a un visitante anónimo a /login.
// OJO: no agregar '/categorias' acá -- ese prefijo SÍ lo comparte el GET
// público con el POST/PUT/DELETE de administración de categorías, y
// meterlo rompería el refresh de sesión de esas pantallas.
const RUTAS_SIN_TOKEN = ['/auth/login', '/auth/registro', '/auth/refresh', '/auth/recuperar', '/catalogo'];

function agregarToken(req: any, token: string | null) {
  if (!token) {
    return req;
  }
  return req.clone({ setHeaders: { Authorization: `Bearer ${token}` } });
}

/**
 * Agrega el JWT a cada request contra la API. Si el backend responde 401
 * (token vencido), intenta refrescar una sola vez y reintenta la request
 * original; si el refresh también falla, cierra la sesión.
 */
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);

  if (!req.url.startsWith(environment.apiUrl)) {
    return next(req);
  }

  const esRutaPublica = RUTAS_SIN_TOKEN.some((ruta) => req.url.includes(ruta));
  const requestConToken = esRutaPublica ? req : agregarToken(req, authService.getAccessToken());

  return next(requestConToken).pipe(
    catchError((error: unknown) => {
      const esNoAutorizado = error instanceof HttpErrorResponse && error.status === 401;
      if (!esNoAutorizado || esRutaPublica) {
        return throwError(() => error);
      }

      return authService.refrescarTokens().pipe(
        switchMap((tokens) => next(agregarToken(req, tokens.access_token))),
        catchError((errorRefresh) => {
          authService.logout();
          return throwError(() => errorRefresh);
        }),
      );
    }),
  );
};
