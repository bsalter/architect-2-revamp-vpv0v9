import { ComponentFixture, TestBed } from '@angular/core/testing'; // @angular/core/testing version 16.2.0
import { By } from '@angular/platform-browser'; // @angular/platform-browser version 16.2.0
import { DebugElement } from '@angular/core'; // @angular/core version 16.2.0

import { ErrorMessageComponent } from './error-message.component';

describe('ErrorMessageComponent', () => {
  let component: ErrorMessageComponent;
  let fixture: ComponentFixture<ErrorMessageComponent>;
  let debugElement: DebugElement;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [ErrorMessageComponent]
    });

    fixture = TestBed.createComponent(ErrorMessageComponent);
    component = fixture.componentInstance;
    debugElement = fixture.debugElement;
  });

  it('should create', () => {
    fixture.detectChanges();
    expect(component).toBeTruthy();
    expect(component.type).toBe('validation');
    expect(component.showIcon).toBeTrue();
  });

  it('should display the error message', () => {
    const testMessage = 'This is a test error message';
    component.message = testMessage;
    fixture.detectChanges();
    
    expect(fixture.nativeElement.textContent).toContain(testMessage);
  });

  it('should apply the correct CSS class based on error type', () => {
    // Test validation type (default)
    component.type = 'validation';
    fixture.detectChanges();
    const rootElement = fixture.nativeElement;
    expect(rootElement.querySelector('.error-message-validation')).toBeTruthy();
    
    // Test warning type
    component.type = 'warning';
    fixture.detectChanges();
    expect(rootElement.querySelector('.error-message-warning')).toBeTruthy();
    
    // Test system type
    component.type = 'system';
    fixture.detectChanges();
    expect(rootElement.querySelector('.error-message-system')).toBeTruthy();
  });

  it('should show icon when showIcon is true', () => {
    component.showIcon = true;
    fixture.detectChanges();
    const iconElement = debugElement.query(By.css('.error-icon'));
    expect(iconElement).toBeTruthy();
  });

  it('should hide icon when showIcon is false', () => {
    component.showIcon = false;
    fixture.detectChanges();
    const iconElement = debugElement.query(By.css('.error-icon'));
    expect(iconElement).toBeNull();
  });

  it('should handle invalid error type gracefully', () => {
    spyOn(console, 'warn');
    
    // Use type assertion to bypass TypeScript type checking for testing
    (component.type as any) = 'invalid-type';
    component.ngOnInit();
    
    expect(console.warn).toHaveBeenCalledWith(
      "ErrorMessageComponent: Invalid type 'invalid-type', falling back to 'validation'"
    );
    expect(component.type).toBe('validation');
  });

  it('should warn when no message is provided', () => {
    component.message = '';
    spyOn(console, 'warn');
    
    component.ngOnInit();
    
    expect(console.warn).toHaveBeenCalledWith(
      'ErrorMessageComponent: No message provided'
    );
  });

  it('should have proper accessibility attributes', () => {
    fixture.detectChanges();
    
    const alertElement = debugElement.query(By.css('[role="alert"]'));
    expect(alertElement).toBeTruthy();
    
    const liveElement = debugElement.query(By.css('[aria-live="assertive"]'));
    expect(liveElement).toBeTruthy();
  });
});