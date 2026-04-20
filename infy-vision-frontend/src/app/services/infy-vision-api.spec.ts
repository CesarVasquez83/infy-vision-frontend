import { InfyVisionApiService } from './infy-vision-api';

describe('InfyVisionApiService', () => {
  let service: InfyVisionApiService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(InfyVisionApiService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
