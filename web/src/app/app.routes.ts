import { Routes } from '@angular/router';
import { authGuard, permisoGuard } from './core/guards';

export const routes: Routes = [
  {
    path: 'login',
    loadComponent: () => import('./features/login/login.component').then((m) => m.LoginComponent),
  },
  {
    path: '',
    loadComponent: () => import('./layout/layout.component').then((m) => m.LayoutComponent),
    canActivate: [authGuard],
    children: [
      { path: '', pathMatch: 'full', redirectTo: 'dashboard' },
      {
        path: 'dashboard',
        loadComponent: () =>
          import('./features/dashboard/dashboard.component').then((m) => m.DashboardComponent),
      },
      {
        path: 'usuarios',
        canActivate: [permisoGuard('usuarios.gestionar')],
        loadComponent: () =>
          import('./features/usuarios/usuarios.component').then((m) => m.UsuariosComponent),
      },
      {
        path: 'roles',
        canActivate: [permisoGuard('roles.gestionar')],
        loadComponent: () => import('./features/roles/roles.component').then((m) => m.RolesComponent),
      },
      {
        path: 'ciudades',
        canActivate: [permisoGuard('organizacion.gestionar')],
        loadComponent: () =>
          import('./features/ciudades/ciudades.component').then((m) => m.CiudadesComponent),
      },
      {
        path: 'sucursales',
        canActivate: [permisoGuard('organizacion.gestionar')],
        loadComponent: () =>
          import('./features/sucursales/sucursales.component').then((m) => m.SucursalesComponent),
      },
      {
        path: 'probador',
        canActivate: [permisoGuard('probador.gestionar')],
        loadComponent: () =>
          import('./features/probador/anclajes-editor.component').then((m) => m.AnclajesEditorComponent),
      },
    ],
  },
  { path: '**', redirectTo: '' },
];
