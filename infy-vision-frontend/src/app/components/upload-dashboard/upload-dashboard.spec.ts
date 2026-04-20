import { Component, Input, OnChanges } from '@angular/core';

@Component({
  selector: 'app-context-engine-panel',
  standalone: true,
  templateUrl: './context-engine-panel.component.html',
  styleUrls: ['./context-engine-panel.component.css']
})
export class ContextEnginePanelComponent implements OnChanges {

  @Input() elite: any;

  radarPoints: string = '';
  driftScore = 0;        // 0–100
  confidenceScore = 50;  // 0–100 (map de alta/media/baja)

  // orden fijo → consistencia visual
  keys = [
    'experience','access','buy_in',
    'trust','decision','delivery',
    'criticality','changes','team_size'
  ];

  ngOnChanges() {
  // 1. Si quieres usar escala humana:
  if (!this.elite?.indices_humanos) return;

  const values = this.keys.map(k =>
    this.toNumber(this.elite.indices_humanos[k])
  );

  this.radarPoints = this.buildRadar(values);
  this.driftScore = this.calcDrift(values);
  this.confidenceScore = this.mapConfidence(this.elite.confianza_lectura);
}

  toNumber(v: any): number {
    const n = Number(v);
    return isNaN(n) ? 0 : n;
  }

  // =========================
  // RADAR (SVG polygon)
  // =========================
  buildRadar(values: number[]): string {
    const center = 100;
    const radius = 80;
    const total = values.length;

    return values.map((v, i) => {
      const angle = (2 * Math.PI * i) / total - Math.PI / 2;
      const r = (v / 10) * radius;
      const x = center + r * Math.cos(angle);
      const y = center + r * Math.sin(angle);
      return `${x},${y}`;
    }).join(' ');
  }

  // =========================
  // DRIFT (varianza simple)
  // =========================
  calcDrift(values: number[]): number {
    const avg = values.reduce((a, b) => a + b, 0) / values.length;
    const variance = values.reduce((a, b) => a + Math.pow(b - avg, 2), 0) / values.length;
    return Math.min(100, variance * 10); // escalado simple
  }

  // =========================
  // CONFIDENCE
  // =========================
  mapConfidence(c: string): number {
    switch ((c || '').toLowerCase()) {
      case 'alta': return 85;
      case 'media': return 60;
      case 'baja': return 35;
      default: return 50;
    }
  }
}