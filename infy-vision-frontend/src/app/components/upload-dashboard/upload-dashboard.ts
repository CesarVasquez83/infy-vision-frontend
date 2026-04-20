import { Component } from '@angular/core';
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

  // Preview de imagen
  imagePreviewUrl: string | null = null;

  constructor(private api: InfyVisionApiService) {}

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.selectedFile = input.files?.[0] ?? null;

    // Generar preview URL
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
        this.result = res;
        this.loading = false;

        // Extraer tabla de KPIs — soporta tanto array directo como nested bajo kpi_table
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

        // Extraer textos del analisis_experto
        const experto = (res as any)?.standard?.analisis_experto ?? {};
        this.observaciones = [];
        this.recomendaciones = [];
        this.riesgos = [];

        const extraerStrings = (val: any): string[] => {
          if (typeof val === 'string') return [val];
          if (Array.isArray(val)) return val.filter(s => typeof s === 'string');
          if (typeof val === 'object' && val !== null)
            return Object.values(val).filter(s => typeof s === 'string') as string[];
          return [];
        };

        const EXCLUIR = ['indices_idoneidad', 'tendencias_agil', 'observaciones_suitability'];

        for (const [key, val] of Object.entries(experto)) {
          if (EXCLUIR.includes(key)) continue;
          if (key === 'recomendaciones' || key === 'recomendacion')
            this.recomendaciones.push(...extraerStrings(val));
          else if (key === 'riesgos' || key === 'riesgos_identificados')
            this.riesgos.push(...extraerStrings(val));
          else if (typeof val === 'string')
            this.observaciones.push(val);
        }

        for (const [seccionKey, seccion] of Object.entries(experto)) {
          if ([...EXCLUIR, 'recomendaciones', 'recomendacion', 'riesgos', 'riesgos_identificados'].includes(seccionKey)) continue;
          if (typeof seccion !== 'object' || seccion === null || Array.isArray(seccion)) continue;
          for (const [key, val] of Object.entries(seccion as any)) {
            if (key === 'recomendaciones' || key === 'recomendacion')
              this.recomendaciones.push(...extraerStrings(val));
            else if (key === 'riesgos')
              this.riesgos.push(...extraerStrings(val));
            else
              this.observaciones.push(...extraerStrings(val));
          }
        }
      },
      error: () => {
        this.error = 'Error al analizar el dashboard.';
        this.loading = false;
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

  // Clase CSS según estado del KPI
  getEstadoClass(estado: string): string {
    const e = (estado ?? '').toLowerCase();
    if (e === 'verde' || e === 'green')   return 'estado-verde';
    if (e === 'amarillo' || e === 'yellow') return 'estado-amarillo';
    if (e === 'rojo' || e === 'red')      return 'estado-rojo';
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
}
