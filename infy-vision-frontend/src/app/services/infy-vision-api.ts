import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { EliteResponse, AnalysisListItem } from '../models/analysis.models';

@Injectable({ providedIn: 'root' })
export class InfyVisionApiService {
  private readonly baseUrl = 'https://infy-vision-backend.jollyforest-eba4f0d9.eastus.azurecontainerapps.io';

  constructor(private http: HttpClient) {}

  // POST → análisis ELITE completo
  uploadDashboardImage(file: File, descripcion: string): Observable<EliteResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('descripcion', descripcion);

    return this.http.post<EliteResponse>(
      `${this.baseUrl}/vision-analysis/elite`,
      formData
    );
  }

  // GET → listado histórico
  getAnalisis(): Observable<AnalysisListItem[]> {
    return this.http.get<AnalysisListItem[]>(
      `${this.baseUrl}/analisis`
    );
  }
}
