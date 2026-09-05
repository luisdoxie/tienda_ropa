import { HttpClient } from '@angular/common/http';
import { Injectable, computed, signal } from '@angular/core';
import { Router } from '@angular/router';
import { Observable, tap } from 'rxjs';
import { environment } from '../../environments/environment';
import { RecuperarRespuesta, RegistroRequest, TokenRespuesta, Usuario, UsuarioYo } from './models/seguridad.models';

const CLAVE_ACCESS_TOKEN = 'fs_access_token';
const CLAVE_REFRESH_TOKEN = 'fs_refresh_token';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly usuarioActual = signal<UsuarioYo | null>(null);

  readonly usuario = this.usuarioActual.asReadonly();
  readonly estaAutenticado = computed(() => this.usuarioActual() !== null);
  readonly permisos = computed(() => this.usuarioActual()?.permisos ?? []);
  readonly roles = computed(() => this.usuarioActual()?.roles ?? []);

  constructor(
    private readonly http: HttpClient,
    private readonly router: Router,
  ) {}

  tienePermiso(codigo: string): boolean {
    return this.permisos().includes(codigo);
  }

  login(email: string, password: string): Observable<TokenRespuesta> {
    return this.http
      .post<TokenRespuesta>(`${environment.apiUrl}/auth/login`, { email, password })
      .pipe(
        tap((tokens) => {
          this.guardarTokens(tokens);
        }),
      );
  }

  /** Recarga el usuario (roles y permisos reales) desde /auth/yo. */
  cargarUsuarioActual(): Observable<UsuarioYo> {
    return this.http
      .get<UsuarioYo>(`${environment.apiUrl}/auth/yo`)
      .pipe(tap((usuario) => this.usuarioActual.set(usuario)));
  }

  /** Se llama al iniciar la app: si hay tokens guardados, restaura la sesión. */
  restaurarSesion(): Observable<UsuarioYo> | null {
    if (!this.getAccessToken()) {
      return null;
    }
    return this.cargarUsuarioActual();
  }

  registrar(datos: RegistroRequest): Observable<Usuario> {
    return this.http.post<Usuario>(`${environment.apiUrl}/auth/registro`, datos);
  }

  solicitarRecuperacion(email: string): Observable<RecuperarRespuesta> {
    return this.http.post<RecuperarRespuesta>(`${environment.apiUrl}/auth/recuperar`, { email });
  }

  confirmarRecuperacion(token: string, password: string): Observable<{ detail: string }> {
    return this.http.post<{ detail: string }>(`${environment.apiUrl}/auth/recuperar/confirmar`, {
      token,
      password,
    });
  }

  logout(): void {
    localStorage.removeItem(CLAVE_ACCESS_TOKEN);
    localStorage.removeItem(CLAVE_REFRESH_TOKEN);
    this.usuarioActual.set(null);
    this.router.navigate(['/login']);
  }

  refrescarTokens(): Observable<TokenRespuesta> {
    const refreshToken = this.getRefreshToken();
    return this.http
      .post<TokenRespuesta>(`${environment.apiUrl}/auth/refresh`, { refresh_token: refreshToken })
      .pipe(tap((tokens) => this.guardarTokens(tokens)));
  }

  guardarTokens(tokens: TokenRespuesta): void {
    localStorage.setItem(CLAVE_ACCESS_TOKEN, tokens.access_token);
    localStorage.setItem(CLAVE_REFRESH_TOKEN, tokens.refresh_token);
  }

  getAccessToken(): string | null {
    return localStorage.getItem(CLAVE_ACCESS_TOKEN);
  }

  getRefreshToken(): string | null {
    return localStorage.getItem(CLAVE_REFRESH_TOKEN);
  }
}
