import { ComponentFixture, TestBed } from '@angular/core/testing'; // v16.2.0
import { DebugElement } from '@angular/core'; // v16.2.0
import { By } from '@angular/platform-browser'; // v16.2.0
import { CommonModule } from '@angular/common'; // v16.2.0

import { LoadingIndicatorComponent } from './loading-indicator.component';

describe('LoadingIndicatorComponent', () => {
  let component: LoadingIndicatorComponent;
  let fixture: ComponentFixture<LoadingIndicatorComponent>;
  let debugElement: DebugElement;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [CommonModule],
      declarations: [LoadingIndicatorComponent]
    });
    fixture = TestBed.createComponent(LoadingIndicatorComponent);
    component = fixture.componentInstance;
    debugElement = fixture.debugElement;
    fixture.detectChanges();
  });

  it('should create the component', () => {
    expect(component).toBeTruthy();
  });

  it('should have default values when initialized', () => {
    expect(component.show).toBe(true);
    expect(component.showText).toBe(true);
    expect(component.text).toBe('Loading...');
    expect(component.size).toBe('medium');
    expect(component.fullscreen).toBe(false);
    expect(component.inline).toBe(false);
    expect(component.ariaLabel).toBe('Loading content, please wait');
  });

  it('should not display when show is false', () => {
    component.show = false;
    fixture.detectChanges();
    const container = debugElement.query(By.css('.loading-indicator-container'));
    expect(container).toBeNull();
  });

  it('should not display text when showText is false', () => {
    component.showText = false;
    fixture.detectChanges();
    const textElement = debugElement.query(By.css('.loading-text'));
    expect(textElement).toBeNull();
  });

  it('should display custom text when provided', () => {
    const customText = 'Custom loading message';
    component.text = customText;
    fixture.detectChanges();
    const textElement = debugElement.query(By.css('.loading-text'));
    expect(textElement.nativeElement.textContent).toContain(customText);
  });

  it('should apply correct size classes', () => {
    // Test small size
    component.size = 'small';
    fixture.detectChanges();
    let spinner = debugElement.query(By.css('.spinner'));
    expect(spinner.classes['spinner-sm']).toBeTruthy();

    // Test medium size
    component.size = 'medium';
    fixture.detectChanges();
    spinner = debugElement.query(By.css('.spinner'));
    expect(spinner.classes['spinner-md']).toBeTruthy();

    // Test large size
    component.size = 'large';
    fixture.detectChanges();
    spinner = debugElement.query(By.css('.spinner'));
    expect(spinner.classes['spinner-lg']).toBeTruthy();

    // Test default when unrecognized size provided
    component.size = 'unknown';
    fixture.detectChanges();
    spinner = debugElement.query(By.css('.spinner'));
    expect(spinner.classes['spinner-md']).toBeTruthy();
  });

  it('should apply fullscreen class when enabled', () => {
    component.fullscreen = true;
    fixture.detectChanges();
    const container = debugElement.query(By.css('.loading-indicator-container'));
    expect(container.classes['fullscreen']).toBeTruthy();
  });

  it('should apply inline class when enabled', () => {
    component.inline = true;
    fixture.detectChanges();
    const container = debugElement.query(By.css('.loading-indicator-container'));
    expect(container.classes['inline']).toBeTruthy();
  });

  it('should set correct aria-label attribute', () => {
    const customLabel = 'Custom loading state';
    component.ariaLabel = customLabel;
    fixture.detectChanges();
    const container = debugElement.query(By.css('.loading-indicator-container'));
    expect(container.attributes['aria-label']).toBe(customLabel);
  });

  it('should correctly implement getContainerClasses method', () => {
    // Default state
    let classes = component.getContainerClasses();
    expect(classes['loading-indicator-container']).toBe(true);
    expect(classes['fullscreen']).toBe(false);
    expect(classes['inline']).toBe(false);

    // Fullscreen enabled
    component.fullscreen = true;
    classes = component.getContainerClasses();
    expect(classes['fullscreen']).toBe(true);

    // Inline enabled
    component.fullscreen = false;
    component.inline = true;
    classes = component.getContainerClasses();
    expect(classes['fullscreen']).toBe(false);
    expect(classes['inline']).toBe(true);

    // Both enabled
    component.fullscreen = true;
    component.inline = true;
    classes = component.getContainerClasses();
    expect(classes['fullscreen']).toBe(true);
    expect(classes['inline']).toBe(true);
  });

  it('should correctly implement getSizeClass method', () => {
    // Small size
    component.size = 'small';
    expect(component.getSizeClass()).toBe('spinner-sm');

    // Medium size
    component.size = 'medium';
    expect(component.getSizeClass()).toBe('spinner-md');

    // Large size
    component.size = 'large';
    expect(component.getSizeClass()).toBe('spinner-lg');

    // Default for unknown size
    component.size = 'unknown';
    expect(component.getSizeClass()).toBe('spinner-md');
  });
});