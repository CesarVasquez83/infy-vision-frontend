import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AnalysisDetail } from './analysis-detail';

describe('AnalysisDetail', () => {
  let component: AnalysisDetail;
  let fixture: ComponentFixture<AnalysisDetail>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AnalysisDetail],
    }).compileComponents();

    fixture = TestBed.createComponent(AnalysisDetail);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
