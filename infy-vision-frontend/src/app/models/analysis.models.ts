// analysis.models.ts — adaptado a INFY VISION backend v3.3.0

export interface DescripcionHorizontal {
  team?: { [key: string]: string };
  culture?: { [key: string]: string };
  project?: { [key: string]: string };
  [key: string]: any;
}

export interface AnalisisExperto {
  observaciones?: string[];
  recomendaciones?: string[];
  [key: string]: any;
}

export interface SuitabilityIndexes {
  experience?: number;
  access?: number;
  buy_in?: number;
  trust?: number;
  decision?: number;
  delivery?: number;
  criticality?: number;
  changes?: number;
  team_size?: number | null;
}

export interface StandardBlock {
  descripcion_horizontal: DescripcionHorizontal;
  analisis_experto: AnalisisExperto;
}

export interface EliteBlock {
  approach_infy: string;
  framework_detectado: string | null;
  suitability_indexes: SuitabilityIndexes;
  veredicto: string;
  suitability_more_pred: boolean;
  suitability_less_pred: boolean;
  suitability_mismatch: boolean;
  suitability_note: string;
  confianza_lectura: string;
  notas_lectura: string;
  kpis_detectados: { [key: string]: number };
}

export interface EliteResponse {
  mode: 'ELITE';
  standard: StandardBlock;
  elite: EliteBlock;
}

// Para el listado histórico
export interface AnalysisListItem {
  id: number;
  filename: string;
  creado_en: string;
}
