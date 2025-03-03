import { ComponentFixture, TestBed } from '@angular/core/testing'; // @angular/core/testing version 16.2.0
import { DebugElement } from '@angular/core'; // @angular/core version 16.2.0
import { By } from '@angular/platform-browser'; // @angular/platform-browser version 16.2.0

import { FooterComponent } from './footer.component';
import { AppConfigService } from '../../../core/config/app-config.service';

describe('FooterComponent', () => {
  let component: FooterComponent;
  let fixture: ComponentFixture<FooterComponent>;
  let debugElement: DebugElement;
  let mockAppConfigService: jasmine.SpyObj<AppConfigService>;

  beforeEach(async () => {
    // Create a spy object for AppConfigService
    mockAppConfigService = jasmine.createSpyObj('AppConfigService', ['getConfig', 'isProduction']);
    
    // Set default return values
    mockAppConfigService.getConfig.and.returnValue({ version: '1.0.0' });
    mockAppConfigService.isProduction.and.returnValue(false);

    await TestBed.configureTestingModule({
      declarations: [FooterComponent],
      providers: [
        { provide: AppConfigService, useValue: mockAppConfigService }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(FooterComponent);
    component = fixture.componentInstance;
    debugElement = fixture.debugElement;
    fixture.detectChanges();
  });

  it('should create the component', () => {
    expect(component).toBeTruthy();
  });

  it('should display the current year in the copyright notice', () => {
    const currentYear = new Date().getFullYear();
    
    // Check component property
    expect(component.currentYear).toBe(currentYear);
    
    // Check rendered text
    const footerElement = fixture.nativeElement;
    expect(footerElement.textContent).toContain(currentYear.toString());
  });

  it('should display the version when available', () => {
    // Check component property
    expect(component.version).toBe('1.0.0');
    
    // Check rendered text
    const footerElement = fixture.nativeElement;
    expect(footerElement.textContent).toContain('1.0.0');
  });

  it('should hide the version when not available', () => {
    // Reset and reconfigure mocks for this specific test
    mockAppConfigService.getConfig.and.returnValue({});
    
    // Re-initialize the component
    component.ngOnInit();
    fixture.detectChanges();
    
    // Check component property falls back to default value
    if (component.isProduction) {
      expect(component.version).toBe('1.0.0');
    } else {
      expect(component.version).toBe('Development');
    }
  });

  it('should handle production mode correctly', () => {
    // Reset and reconfigure mocks for production mode
    mockAppConfigService.getConfig.and.returnValue({});
    mockAppConfigService.isProduction.and.returnValue(true);
    
    // Re-initialize the component
    component.ngOnInit();
    fixture.detectChanges();
    
    expect(component.isProduction).toBeTrue();
    expect(component.version).toBe('1.0.0');
    
    // Check rendered text
    const footerElement = fixture.nativeElement;
    expect(footerElement.textContent).toContain('1.0.0');
  });

  it('should get version from AppConfigService', () => {
    const testVersion = '2.0.0-beta';
    mockAppConfigService.getConfig.and.returnValue({ version: testVersion });
    
    // Re-initialize component to get new config
    component.ngOnInit();
    fixture.detectChanges();
    
    // Verify service was called and version was set correctly
    expect(mockAppConfigService.getConfig).toHaveBeenCalled();
    expect(component.version).toBe(testVersion);
    
    // Check rendered text
    const footerElement = fixture.nativeElement;
    expect(footerElement.textContent).toContain(testVersion);
  });
});