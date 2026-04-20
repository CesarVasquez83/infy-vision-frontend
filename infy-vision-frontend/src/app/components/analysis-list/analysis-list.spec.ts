import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AnalysisList } from './analysis-list';

describe('AnalysisList', () => {
  let component: AnalysisList;
  let fixture: ComponentFixture<AnalysisList>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AnalysisList],
    }).compileComponents();

    fixture = TestBed.createComponent(AnalysisList);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
