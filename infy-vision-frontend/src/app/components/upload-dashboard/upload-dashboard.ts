import { Component, ChangeDetectorRef, NgZone } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { InfyVisionApiService } from '../../services/infy-vision-api';
import { EliteResponse, SuitabilityIndexes } from '../../models/analysis.models';
import { ContextEnginePanelComponent } from '../context-engine-panel/context-engine-panel.component';

@Component({
  selector: 'app-upload-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule, ContextEnginePanelComponent],
  templateUrl: './upload-dashboard.html',
  styleUrls: ['./upload-dashboard.css']
})
export class UploadDashboard {

  selectedFile: File | null = null;
  descripcion = '';
  loading = false;
  error: string | null = null;
  result: EliteResponse | null = null;
  tablaSuperior: any[] = [];
  observaciones: string[] = [];
  recomendaciones: string[] = [];
  riesgos: string[] = [];
  quickReading: string = '';
  imagePreviewUrl: string | null = null;

  constructor(
    private api: InfyVisionApiService,
    private cdr: ChangeDetectorRef,
    private ngZone: NgZone
  ) {}

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.selectedFile = input.files?.[0] ?? null;
    if (this.selectedFile) {
      if (this.imagePreviewUrl) {
        URL.revokeObjectURL(this.imagePreviewUrl);
      }
      this.imagePreviewUrl = URL.createObjectURL(this.selectedFile);
    } else {
      this.imagePreviewUrl = null;
    }
  }

  onSubmit(): void {
    if (!this.selectedFile) {
      this.error = 'Selecciona una imagen primero.';
      return;
    }
    this.loading = true;
    this.error = null;
    this.result = null;

    this.api.uploadDashboardImage(this.selectedFile, this.descripcion).subscribe({
      next: (res) => {
        this.ngZone.run(() => {
          this.result = res;
          this.loading = false;
          this.quickReading = (res as any)?.standard?.descripcion_horizontal?.quick_reading ?? '';

          const descH = (res as any)?.standard?.descripcion_horizontal ?? {};
          const kpis: any[] = Array.isArray(descH)
            ? descH
            : (descH.tabla_kpis ?? descH.kpi_table ?? descH.tabla ?? []);

          this.tablaSuperior = kpis.map((kpi: any) => ({
            proyecto:       kpi.proyecto,
            marco:          kpi.marco,
            dimension:      kpi.dimension,
            kpi:            kpi.kpi,
            denominacion:   kpi.denominacion_kpi ?? kpi.denominacion_de_kpi,
            valor:          kpi.valor,
            unidad:         kpi.unidad,
            umbralVerde:    kpi.umbral_verde,
            umbralAmarillo: kpi.umbral_amarillo,
            estado:         kpi.estado,
            queMide:        kpi.que_mide
          }));

          const experto = (res as any)?.standard?.analisis_experto ?? {};

          this.observaciones = Array.isArray(experto.observaciones)
            ? experto.observaciones
            : experto.observaciones_generales
              ? [experto.observaciones_generales]
              : [];

          this.recomendaciones = Array.isArray(experto.recomendaciones) ? experto.recomendaciones : [];
          this.riesgos = Array.isArray(experto.riesgos) ? experto.riesgos : [];

          this.cdr.detectChanges();
        });
      },
      error: () => {
        this.ngZone.run(() => {
          this.error = 'Error al analizar el dashboard.';
          this.loading = false;
          this.cdr.detectChanges();
        });
      }
    });
  }

  toNumber(val: unknown): number {
    return typeof val === 'number' ? val : 0;
  }

  getColor(value: number): string {
    if (value >= 7) return 'good';
    if (value >= 4) return 'medium';
    return 'bad';
  }

  getEstadoClass(estado: string): string {
    const e = (estado ?? '').toLowerCase();
    if (e === 'verde' || e === 'green')     return 'estado-verde';
    if (e === 'amarillo' || e === 'yellow') return 'estado-amarillo';
    if (e === 'rojo' || e === 'red')        return 'estado-rojo';
    return 'estado-info';
  }

  suitabilityKeys(): (keyof SuitabilityIndexes)[] {
    return [
      'experience', 'access', 'buy_in', 'trust',
      'decision', 'delivery', 'criticality', 'changes', 'team_size'
    ];
  }

  suitabilityLabel(key: string): string {
    const labels: { [k: string]: string } = {
      experience: 'Experiencia',
      access: 'Acceso',
      buy_in: 'Aceptación',
      trust: 'Confianza',
      decision: 'Toma de decisiones',
      delivery: 'Entrega',
      criticality: 'Criticidad',
      changes: 'Cambios',
      team_size: 'Tamaño del Equipo'
    };
    return labels[key] ?? key;
  }

  suitabilityFloro(key: string): string {
    const floros: { [k: string]: string } = {
      experience: 'ALTO = (Predictivo, poca experiencia en ágil) / BAJO = (Ágil, más experiencia en entornos ágiles)',
      access: 'ALTO = (Predictivo, menos acceso a cliente) / BAJO = (Ágil, hay mayor acceso a cliente)',
      trust: 'BAJO = (Ágil, mayor confianza en el equipo) / ALTO = (Predictivo, falta de confianza en el equipo)',
      decision: 'BAJO = (Ágil, decisiones rápidas distribuidas) / ALTO = (jerárquico, más predictivo)',
      buy_in: 'ALTO = (Predictivo, poca aceptación de autonomía del team) / BAJO = (Ágil, aceptan autonomía del equipo)',
      team_size: 'BAJO = (Ágil; se maneja grupos pequeños) / ALTO = (Predictivo, generalmente grupos numerosos)',
      changes: 'BAJO = (Ágil; alta incertidumbre) / ALTO = (Predictivo, debido a pocos cambios)',
      criticality: 'ALTO = (Predictivo, riesgo alto) / BAJO = (Ágil; tolerante a error)',
      delivery: 'BAJO = (Ágil, prueba entrega incremental) / ALTO = (Predictivo, prefiere única entrega)',
    };
    return floros[key] ?? '';
  }

  formatKpiKey(key: string): string {
    return key
      .replace(/_/g, ' ')
      .replace(/\b\w/g, c => c.toUpperCase());
  }
}
