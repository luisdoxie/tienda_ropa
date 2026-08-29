import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { MessageService } from 'primeng/api';
import { catchError, throwError } from 'rxjs';

function mensajeDe(error: HttpErrorResponse): string {
  const detalle = error.error?.detail;
  if (typeof detalle === 'string') {
    return detalle;
  }
  if (Array.isArray(detalle)) {
    // Errores de validación de Pydantic/FastAPI (422).
    return detalle.map((e: any) => e.msg ?? String(e)).join(' · ');
  }
  if (error.status === 0) {
    return 'No se pudo conectar con el servidor.';
  }
  return 'Ocurrió un error inesperado.';
}

/**
 * Muestra un toast con cualquier error HTTP que llegue hasta acá. El 401
 * que el authInterceptor logra recuperar reintentando con un token nuevo
 * nunca llega a este interceptor.
 */
export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const messageService = inject(MessageService);

  return next(req).pipe(
    catchError((error: unknown) => {
      if (error instanceof HttpErrorResponse && error.status !== 401) {
        messageService.add({
          severity: 'error',
          summary: `Error ${error.status || ''}`.trim(),
          detail: mensajeDe(error),
        });
      }
      return throwError(() => error);
    }),
  );
};
