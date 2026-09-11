import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from './auth.service';

export const authGuard: CanActivateFn = (_route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (authService.estaAutenticado()) {
    return true;
  }
  return router.createUrlTree(['/login'], { queryParams: { returnTo: state.url } });
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

/**
 * Protege la raíz del back office: un cliente autenticado (rol único
 * "cliente") nunca debe ver ninguna pantalla de administración, ni
 * escribiendo la URL a mano. Reemplaza a `authGuard` en esa ruta.
 */
export const staffGuard: CanActivateFn = () => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (!authService.estaAutenticado()) {
    return router.parseUrl('/login');
  }
  const roles = authService.roles();
  // Sin ningún rol de staff (incluye roles.length === 0, un usuario
  // logueado cuya asignación de roles quedó desincronizada) no hay nada
  // que autorice el back office -- antes, roles.length === 0 caía al
  // `return true` final y dejaba entrar a cualquiera sin permisos reales.
  const esStaff = roles.some((rol) => rol !== 'cliente');
  if (!esStaff) {
    return router.parseUrl('/catalogo');
  }
  return true;
};
