import { DecimalPipe } from '@angular/common';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { MessageService } from 'primeng/api';
import { environment } from '../../../environments/environment';
import { Categoria, CatalogoItem } from '../../core/models/catalogo.models';

const DEMORA_BUSQUEDA_MS = 350;

@Component({
  selector: 'app-catalogo-publico',
  standalone: true,
  imports: [DecimalPipe, FormsModule, RouterLink],
  templateUrl: './catalogo-publico.component.html',
  styleUrl: './catalogo-publico.component.scss',
})
export class CatalogoPublicoComponent implements OnInit {
  private readonly http = inject(HttpClient);
  private readonly messageService = inject(MessageService);
  private temporizadorBusqueda?: ReturnType<typeof setTimeout>;

  protected readonly categorias = signal<Categoria[]>([]);
  protected readonly productos = signal<CatalogoItem[]>([]);
  protected readonly cargando = signal(true);
  protected readonly error = signal(false);

  protected texto = '';
  protected readonly categoriaSeleccionada = signal<number | null>(null);

  ngOnInit(): void {
    this.cargarCategorias();
    this.cargarProductos();
  }

  private cargarCategorias(): void {
    this.http.get<Categoria[]>(`${environment.apiUrl}/categorias`).subscribe({
      next: (categorias) => this.categorias.set(categorias),
      // Las categorías son un extra sobre el hero -- si fallan, el
      // catálogo en sí sigue siendo navegable, así que no se muestra
      // error por esto.
      error: () => this.categorias.set([]),
    });
  }

  protected cargarProductos(): void {
    this.cargando.set(true);
    this.error.set(false);

    const texto = this.texto.trim();
    const categoriaId = this.categoriaSeleccionada();
    const url =
      texto || categoriaId !== null
        ? `${environment.apiUrl}/catalogo/buscar?${this.armarParametros(texto, categoriaId)}`
        : `${environment.apiUrl}/catalogo`;

    this.http.get<CatalogoItem[]>(url).subscribe({
      next: (productos) => {
        this.productos.set(productos);
        this.cargando.set(false);
      },
      error: (err: HttpErrorResponse) => {
        this.cargando.set(false);
        this.error.set(true);
        if (err.status !== 429) {
          this.messageService.add({
            severity: 'error',
            summary: 'No se pudo cargar el catálogo',
            detail: 'Probá de nuevo en un momento.',
          });
        }
      },
    });
  }

  private armarParametros(texto: string, categoriaId: number | null): string {
    const params = new URLSearchParams();
    if (texto) params.set('q', texto);
    if (categoriaId !== null) params.set('categoria_id', String(categoriaId));
    return params.toString();
  }

  protected onBuscar(): void {
    clearTimeout(this.temporizadorBusqueda);
    this.temporizadorBusqueda = setTimeout(() => this.cargarProductos(), DEMORA_BUSQUEDA_MS);
  }

  protected seleccionarCategoria(id: number | null): void {
    this.categoriaSeleccionada.set(id);
    this.cargarProductos();
  }
}
