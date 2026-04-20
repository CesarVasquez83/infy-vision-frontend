import { Component, Input, OnChanges } from '@angular/core';
import { CommonModule } from '@angular/common';

const AXIS_LABELS = [
  'Experiencia', 'Acceso', 'Aceptación', 'Confianza',
  'Decisión', 'Entrega', 'Criticidad', 'Cambios'
];

@Component({
  selector: 'app-context-engine-panel',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './context-engine-panel.component.html',
  styleUrls: ['./context-engine-panel.component.css']
})
export class ContextEnginePanelComponent implements OnChanges {

  @Input() elite: any;

  radarPoints = '';
  driftScore = 0;
  confidenceScore = 50;
  axisLines: { x: number; y: number }[] = [];
  axisLabels: { x: number; y: number; text: string }[] = [];

  ngOnChanges() {
    console.log('ELITE DATA 👉', this.elite);

    if (!this.elite?.suitability_indexes) {
      console.log('NO HAY SUITABILITY ❌');
      return;
    }

    const s = this.elite.suitability_indexes;

    const values = [
      s.experience ?? 0,
      s.access ?? 0,
      s.buy_in ?? 0,
      s.trust ?? 0,
      s.decision ?? 0,
      s.delivery ?? 0,
      s.criticality ?? 0,
      s.changes ?? 0
    ];

    this.radarPoints = this.buildRadar(values);
    this.axisLines = this.buildAxisLines(values.length);
    this.axisLabels = this.buildAxisLabels(values.length);

    // Drift: desviación promedio respecto al centro (5)
    const avg = values.reduce((a, b) => a + b, 0) / values.length;
    this.driftScore = Math.round(Math.abs(avg - 5) * 20);
    this.confidenceScore = Math.max(0, 100 - this.driftScore);
  }

  buildRadar(values: number[]): string {
    const center = 100;
    const radius = 80;
    const angleStep = (2 * Math.PI) / values.length;

    return values.map((v, i) => {
      const r = (v / 10) * radius;
      const angle = i * angleStep - Math.PI / 2;
      const x = center + r * Math.cos(angle);
      const y = center + r * Math.sin(angle);
      return `${x},${y}`;
    }).join(' ');
  }

  buildAxisLines(count: number): { x: number; y: number }[] {
    const center = 100;
    const radius = 80;
    const angleStep = (2 * Math.PI) / count;

    return Array.from({ length: count }, (_, i) => {
      const angle = i * angleStep - Math.PI / 2;
      return {
        x: center + radius * Math.cos(angle),
        y: center + radius * Math.sin(angle)
      };
    });
  }

  buildAxisLabels(count: number): { x: number; y: number; text: string }[] {
    const center = 100;
    const radius = 95; // un poco más afuera del círculo
    const angleStep = (2 * Math.PI) / count;

    return Array.from({ length: count }, (_, i) => {
      const angle = i * angleStep - Math.PI / 2;
      return {
        x: center + radius * Math.cos(angle),
        y: center + radius * Math.sin(angle),
        text: AXIS_LABELS[i] ?? `Eje ${i + 1}`
      };
    });
  }
}
