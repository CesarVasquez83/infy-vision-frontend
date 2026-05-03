import { Component, OnInit, inject, ChangeDetectorRef } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-analysis-detail',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './analysis-detail.html',
  styleUrl: './analysis-detail.css',
})
export class AnalysisDetail implements OnInit {
  analisis: any = null;
  loading = true;
  error = '';

suitabilityItems() {
  const suit = this.analisis?.analisis_pm?.descripcion_horizontal?.suitability_indexes
            || this.analisis?.analisis_pm?.suitability_indexes;
  if (!suit) return [];
  const floros: any = {
    experience: 'ALTO = (Predictivo, poca experiencia en ágil) / BAJO = (Ágil, más experiencia en entornos ágiles)',
    access: 'ALTO = (Predictivo, menos acceso a cliente) / BAJO = (ÁGIL, hay mayor acceso a cliente)',
    trust: 'BAJO = (Ágil, mayor confianza en el equipo) / ALTO = (Predictivo, falta de confianza en el equipo)',
    decision: 'BAJO = (Ágil, decisiones rápidas distribuidas) / ALTO = (jerárquico, más predictivo)',
    buy_in: 'ALTO = (Predictivo, poca aceptación de autonomía del team) / BAJO = (Ágil, aceptan autonomía del equipo)',
    team_size: 'BAJO = (Ágil; se maneja grupos pequeños) / ALTO = (Predictivo, generalmente grupos numerosos)',
    changes: 'BAJO = (Ágil; alta incertidumbre) / ALTO = (Predictivo, debido a pocos cambios)',
    criticality: 'ALTO = (Predictivo, riesgo alto) / BAJO = (Ágil; tolerante a error)',
    delivery: 'BAJO = (Ágil, prueba entrega incremental) / ALTO = (Predictivo, prefiere única entrega)',
  };
  const labels: any = {
    experience: 'Experiencia', access: 'Acceso', trust: 'Confianza',
    decision: 'Decisión', buy_in: 'Aceptación', team_size: 'Tamaño Equipo',
    changes: 'Cambios', criticality: 'Criticidad', delivery: 'Entrega',
  };
  return Object.entries(suit).map(([k, v]: any) => ({
    label: labels[k] || k,
    valor: v,
    color: v <= 4 ? 'verde' : v <= 8 ? 'amarillo' : 'rojo',
    floro: floros[k] || '',
  }));
}

observacionesFiltradas() {
    const obs = this.analisis?.analisis_pm?.analisis_experto?.observaciones;
    if (!obs) return [];
    return obs.filter((o: string) => !o.trim().match(/^(ALTO|BAJO|Alto|Bajo)/));
}

  private route = inject(ActivatedRoute);
  private http = inject(HttpClient);
  private cdr = inject(ChangeDetectorRef);

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    this.http.get(`https://infy-vision-backend.jollyforest-eba4f0d9.eastus.azurecontainerapps.io/analisis/${id}`).subscribe({
      next: (data) => {
        this.analisis = data;
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        this.error = 'Error cargando análisis.';
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }
}