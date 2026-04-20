import { Routes } from '@angular/router';
import { UploadDashboard } from './components/upload-dashboard/upload-dashboard';
import { AnalysisList } from './components/analysis-list/analysis-list';
import { AnalysisDetail } from './components/analysis-detail/analysis-detail';

export const routes: Routes = [
  { path: '', redirectTo: 'upload', pathMatch: 'full' },
  { path: 'upload', component: UploadDashboard },
  { path: 'analisis', component: AnalysisList },
  { path: 'analisis/:id', component: AnalysisDetail },
  { path: '**', redirectTo: 'upload' }
];
