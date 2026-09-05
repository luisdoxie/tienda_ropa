import { Router } from '@angular/router';
import { AuthService } from './auth.service';

/**
 * A dónde mandar al usuario justo después de loguearse (login o registro +
 * login automático). Si venía de un `authGuard` que lo frenó (`returnTo` en
 * la query), vuelve ahí. Si no, un cliente va a la tienda pública y
 * cualquier otro rol al back office -- ver `staffGuard` en `guards.ts`,
 * que aplica la misma regla para bloquear el acceso directo por URL.
 */
export function navegarDespuesDeLogin(router: Router, authService: AuthService, returnTo: string | null): void {
  if (returnTo) {
    router.navigateByUrl(returnTo);
    return;
  }
  const roles = authService.roles();
  const esSoloCliente = roles.length > 0 && roles.every((rol) => rol === 'cliente');
  router.navigate([esSoloCliente ? '/catalogo' : '/dashboard']);
}
