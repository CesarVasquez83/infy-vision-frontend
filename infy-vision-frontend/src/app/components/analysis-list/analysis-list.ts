import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

import { InfyVisionApiService } from '../../services/infy-vision-api';
import { AnalysisListItem } from '../../models/analysis.models';

@Component({
  selector: 'app-analysis-list',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './analysis-list.html',
  styleUrls: ['./analysis-list.css']
})
export class AnalysisList implements OnInit {

  analisis: AnalysisListItem[] = [];
  loading = true;
  error: string | null = null;

  constructor(private api: InfyVisionApiService) {}

  ngOnInit(): void {
    this.api.getAnalisis().subscribe({
      next: (data) => {
        this.analisis = data;
        this.loading = false;
      },
      error: () => {
        this.error = 'Error al cargar el histórico.';
        this.loading = false;
      }
    });
  }
}
