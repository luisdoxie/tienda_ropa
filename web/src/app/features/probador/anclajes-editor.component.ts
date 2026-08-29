import { HttpClient } from '@angular/common/http';
import { Component, ElementRef, ViewChild, inject, signal, computed } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ButtonModule } from 'primeng/button';
import { InputNumberModule } from 'primeng/inputnumber';
import { InputTextModule } from 'primeng/inputtext';
import { SelectModule } from 'primeng/select';
import { TagModule } from 'primeng/tag';
import { environment } from '../../../environments/environment';
import { Ancla, ActivoProbador, Anclajes, TipoActivoProbador } from '../../core/models/probador.models';

type NombreAncla = keyof Anclajes;

const ORDEN_ANCLAS: NombreAncla[] = ['hombro_izq', 'hombro_der', 'cadera'];

const ETIQUETAS_ANCLA: Record<NombreAncla, string> = {
  hombro_izq: 'Hombro izquierdo',
  hombro_der: 'Hombro derecho',
  cadera: 'Cadera',
};

const TIPOS: { label: string; value: TipoActivoProbador }[] = [
  { label: 'Overlay 2D (modo espejo)', value: 'overlay_2d' },
  { label: 'Flat-lay para IA', value: 'flatlay_ia' },
  { label: 'Miniatura', value: 'thumb' },
];

interface Plantilla {
  nombre: string;
  anclajes: Anclajes;
}

// Proporciones típicas sobre un PNG de prenda superior encuadrada al
// centro. Son un punto de partida para no marcar desde cero cada vez;
// igual se pueden arrastrar después.
const PLANTILLAS: Plantilla[] = [
  {
    nombre: 'Camisa',
    anclajes: {
      hombro_izq: { x: 0.28, y: 0.18 },
      hombro_der: { x: 0.72, y: 0.18 },
      cadera: { x: 0.5, y: 0.62 },
    },
  },
  {
    nombre: 'Polera',
    anclajes: {
      hombro_izq: { x: 0.3, y: 0.15 },
      hombro_der: { x: 0.7, y: 0.15 },
      cadera: { x: 0.5, y: 0.58 },
    },
  },
  {
    nombre: 'Chamarra',
    anclajes: {
      hombro_izq: { x: 0.24, y: 0.16 },
      hombro_der: { x: 0.76, y: 0.16 },
      cadera: { x: 0.5, y: 0.68 },
    },
  },
];

@Component({
  selector: 'app-anclajes-editor',
  standalone: true,
  imports: [FormsModule, ButtonModule, InputTextModule, InputNumberModule, SelectModule, TagModule],
  templateUrl: './anclajes-editor.component.html',
  styleUrl: './anclajes-editor.component.scss',
})
export class AnclajesEditorComponent {
  private readonly http = inject(HttpClient);

  protected readonly tipos = TIPOS;
  protected readonly plantillas = PLANTILLAS;
  protected readonly etiquetas = ETIQUETAS_ANCLA;

  protected readonly varianteId = signal<number | null>(null);
  protected readonly assets = signal<ActivoProbador[]>([]);
  protected readonly assetSeleccionado = signal<ActivoProbador | null>(null);

  protected readonly tipoNuevo = signal<TipoActivoProbador>('overlay_2d');
  protected archivoNuevo: File | null = null;

  protected readonly anclas = signal<Record<NombreAncla, Ancla | null>>({
    hombro_izq: null,
    hombro_der: null,
    cadera: null,
  });
  protected readonly factorAncho = signal(1.18);
  protected arrastrando: NombreAncla | null = null;

  protected readonly siguientePaso = computed<NombreAncla | null>(() => {
    const a = this.anclas();
    return ORDEN_ANCLAS.find((n) => a[n] === null) ?? null;
  });

  protected readonly anclajesCompletos = computed(() => this.siguientePaso() === null);

  protected readonly marcadores = computed(() =>
    ORDEN_ANCLAS.map((nombre) => ({ nombre, ancla: this.anclas()[nombre] })).filter(
      (m): m is { nombre: NombreAncla; ancla: Ancla } => m.ancla !== null,
    ),
  );

  @ViewChild('imagenRef') imagenRef?: ElementRef<HTMLImageElement>;

  // ---- Carga de assets -------------------------------------------------

  cargarAssets(): void {
    const id = this.varianteId();
    if (id === null) return;
    this.http
      .get<ActivoProbador[]>(`${environment.apiUrl}/probador/assets`, { params: { variante_id: id } })
      .subscribe((assets) => this.assets.set(assets));
  }

  seleccionarAsset(asset: ActivoProbador): void {
    this.assetSeleccionado.set(asset);
    if (asset.anclajes) {
      this.anclas.set({ ...asset.anclajes });
    } else {
      this.reiniciarMarcado();
    }
  }

  reiniciarMarcado(): void {
    this.anclas.set({ hombro_izq: null, hombro_der: null, cadera: null });
  }

  aplicarPlantilla(plantilla: Plantilla): void {
    this.anclas.set({ ...plantilla.anclajes });
  }

  // ---- Subida de un asset nuevo ------------------------------------------

  onArchivoSeleccionado(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.archivoNuevo = input.files?.[0] ?? null;
  }

  subirAsset(): void {
    const id = this.varianteId();
    if (id === null || !this.archivoNuevo) return;

    const formulario = new FormData();
    formulario.append('variante_id', String(id));
    formulario.append('tipo', this.tipoNuevo());
    formulario.append('archivo', this.archivoNuevo);

    this.http.post<ActivoProbador>(`${environment.apiUrl}/probador/assets`, formulario).subscribe((asset) => {
      this.archivoNuevo = null;
      this.cargarAssets();
      this.seleccionarAsset(asset);
    });
  }

  // ---- Marcado de anclajes sobre la imagen -------------------------------

  clicEnImagen(event: MouseEvent): void {
    const paso = this.siguientePaso();
    if (!paso || !this.imagenRef) return;

    const { x, y } = this.coordenadasNormalizadas(event.clientX, event.clientY);
    this.anclas.update((actual) => ({ ...actual, [paso]: { x, y } }));
  }

  iniciarArrastre(nombre: NombreAncla, event: MouseEvent): void {
    event.stopPropagation();
    this.arrastrando = nombre;
  }

  moverArrastre(event: MouseEvent): void {
    if (!this.arrastrando || !this.imagenRef) return;
    const { x, y } = this.coordenadasNormalizadas(event.clientX, event.clientY);
    this.anclas.update((actual) => ({ ...actual, [this.arrastrando as NombreAncla]: { x, y } }));
  }

  terminarArrastre(): void {
    this.arrastrando = null;
  }

  private coordenadasNormalizadas(clientX: number, clientY: number): Ancla {
    const rect = this.imagenRef!.nativeElement.getBoundingClientRect();
    // Normalizado respecto al tamaño MOSTRADO de la imagen, no a píxeles
    // absolutos: por eso sigue siendo válido si se redimensiona la
    // ventana o la imagen se muestra más chica o más grande.
    const x = Math.min(1, Math.max(0, (clientX - rect.left) / rect.width));
    const y = Math.min(1, Math.max(0, (clientY - rect.top) / rect.height));
    return { x, y };
  }

  // ---- Vista previa del factor_ancho --------------------------------------

  protected readonly lineaPreview = computed(() => {
    const a = this.anclas();
    if (!a.hombro_izq || !a.hombro_der) return null;

    const dx = a.hombro_der.x - a.hombro_izq.x;
    const dy = a.hombro_der.y - a.hombro_izq.y;
    const cx = (a.hombro_izq.x + a.hombro_der.x) / 2;
    const cy = (a.hombro_izq.y + a.hombro_der.y) / 2;
    const factor = this.factorAncho();

    return {
      x1: cx - (dx / 2) * factor,
      y1: cy - (dy / 2) * factor,
      x2: cx + (dx / 2) * factor,
      y2: cy + (dy / 2) * factor,
    };
  });

  // ---- Guardar y validar --------------------------------------------------

  guardarAnclajes(): void {
    const asset = this.assetSeleccionado();
    const a = this.anclas();
    if (!asset || !this.anclajesCompletos()) return;

    const payload: Anclajes = {
      hombro_izq: a.hombro_izq!,
      hombro_der: a.hombro_der!,
      cadera: a.cadera!,
    };

    this.http
      .put<ActivoProbador>(`${environment.apiUrl}/probador/assets/${asset.id}/anclajes`, payload)
      .subscribe((actualizado) => {
        this.assetSeleccionado.set(actualizado);
        this.cargarAssets();
      });
  }

  validarAsset(): void {
    const asset = this.assetSeleccionado();
    if (!asset) return;
    this.http
      .put<ActivoProbador>(`${environment.apiUrl}/probador/assets/${asset.id}/validar`, {})
      .subscribe((actualizado) => {
        this.assetSeleccionado.set(actualizado);
        this.cargarAssets();
      });
  }
}
