import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from './auth.service';

export const authGuard: CanActivateFn = () => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (authService.estaAutenticado()) {
    return true;
  }
  return router.parseUrl('/login');
};

/** Guarda de ruta por permiso (p. ej. "roles.gestionar"). */
export function permisoGuard(permiso: string): CanActivateFn {
  return () => {
    const authService = inject(AuthService);
    const router = inject(Router);

    if (!authService.estaAutenticado()) {
      return router.parseUrl('/login');
    }
    if (!authService.tienePermiso(permiso)) {
      return router.parseUrl('/dashboard');
    }
    return true;
  };
}
