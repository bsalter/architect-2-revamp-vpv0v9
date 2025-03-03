import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing'; // @angular/core/testing v16.2.0
import { By } from '@angular/platform-browser'; // @angular/platform-browser v16.2.0
import { NoopAnimationsModule } from '@angular/platform-browser/animations'; // @angular/platform-browser/animations v16.2.0
import { BehaviorSubject } from 'rxjs'; // rxjs v7.8.1

import { ToastComponent } from './toast.component';
import { ToastService } from '../../services/toast.service';

// Create mock ToastService for testing
class MockToastService {
  private toastsSubject = new BehaviorSubject<any[]>([]);

  getToasts() {
    return this.toastsSubject.asObservable();
  }

  showSuccess(message: string, options: any = {}) {
    const toast = {
      type: 'success',
      message,
      title: options.title || 'Success',
      duration: options.duration || 5000,
      timestamp: Date.now()
    };
    const currentToasts = this.toastsSubject.getValue();
    this.toastsSubject.next([...currentToasts, toast]);
  }

  showError(message: string, options: any = {}) {
    const toast = {
      type: 'error',
      message,
      title: options.title || 'Error',
      duration: options.duration || 5000,
      timestamp: Date.now()
    };
    const currentToasts = this.toastsSubject.getValue();
    this.toastsSubject.next([...currentToasts, toast]);
  }

  showWarning(message: string, options: any = {}) {
    const toast = {
      type: 'warning',
      message,
      title: options.title || 'Warning',
      duration: options.duration || 5000,
      timestamp: Date.now()
    };
    const currentToasts = this.toastsSubject.getValue();
    this.toastsSubject.next([...currentToasts, toast]);
  }

  showInfo(message: string, options: any = {}) {
    const toast = {
      type: 'info',
      message,
      title: options.title || 'Information',
      duration: options.duration || 5000,
      timestamp: Date.now()
    };
    const currentToasts = this.toastsSubject.getValue();
    this.toastsSubject.next([...currentToasts, toast]);
  }

  clear() {
    const clearAction = {
      type: 'clear',
      message: '',
      title: '',
      duration: 0,
      timestamp: Date.now(),
      isCloseAction: true
    };
    this.toastsSubject.next([clearAction]);
  }

  remove(timestamp: number) {
    const currentToasts = this.toastsSubject.getValue();
    const filteredToasts = currentToasts.filter(toast => toast.timestamp !== timestamp);
    this.toastsSubject.next(filteredToasts);
  }
}

describe('ToastComponent', () => {
  let component: ToastComponent;
  let fixture: ComponentFixture<ToastComponent>;
  let toastService: MockToastService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [ToastComponent],
      imports: [NoopAnimationsModule],
      providers: [
        { provide: ToastService, useClass: MockToastService }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(ToastComponent);
    component = fixture.componentInstance;
    toastService = TestBed.inject(ToastService) as unknown as MockToastService;
    fixture.detectChanges();
  });

  it('should create the component', () => {
    expect(component).toBeTruthy();
  });

  it("should have default position set to 'toast-top-right'", () => {
    expect(component.position).toBe('toast-top-right');
  });

  it('should display toast messages from the service', () => {
    toastService.showSuccess('Test success message');
    fixture.detectChanges();
    
    const toastElements = fixture.debugElement.queryAll(By.css('.toast'));
    expect(toastElements.length).toBe(1);
    expect(toastElements[0].nativeElement.textContent).toContain('Test success message');
  });

  it('should display multiple toast messages', () => {
    toastService.showSuccess('Success message');
    toastService.showError('Error message');
    toastService.showWarning('Warning message');
    fixture.detectChanges();
    
    const toastElements = fixture.debugElement.queryAll(By.css('.toast'));
    expect(toastElements.length).toBe(3);
  });

  it('should apply correct CSS classes based on toast type', () => {
    toastService.showSuccess('Success message');
    toastService.showError('Error message');
    toastService.showWarning('Warning message');
    toastService.showInfo('Info message');
    fixture.detectChanges();
    
    const toastElements = fixture.debugElement.queryAll(By.css('.toast'));
    
    expect(toastElements[0].nativeElement.classList.contains('toast-success')).toBeTruthy();
    expect(toastElements[1].nativeElement.classList.contains('toast-error')).toBeTruthy();
    expect(toastElements[2].nativeElement.classList.contains('toast-warning')).toBeTruthy();
    expect(toastElements[3].nativeElement.classList.contains('toast-info')).toBeTruthy();
  });

  it('should display the correct icon based on toast type', () => {
    toastService.showSuccess('Success message');
    toastService.showError('Error message');
    toastService.showWarning('Warning message');
    toastService.showInfo('Info message');
    fixture.detectChanges();
    
    const successIcon = fixture.debugElement.query(By.css('.toast-success .toast-icon'));
    const errorIcon = fixture.debugElement.query(By.css('.toast-error .toast-icon'));
    const warningIcon = fixture.debugElement.query(By.css('.toast-warning .toast-icon'));
    const infoIcon = fixture.debugElement.query(By.css('.toast-info .toast-icon'));
    
    expect(successIcon).toBeTruthy();
    expect(errorIcon).toBeTruthy();
    expect(warningIcon).toBeTruthy();
    expect(infoIcon).toBeTruthy();
  });

  it('should close a toast when the close button is clicked', () => {
    toastService.showSuccess('Test message');
    fixture.detectChanges();
    
    // Spy on closeToast method
    spyOn(component, 'closeToast').and.callThrough();
    
    // Find and click close button
    const closeButton = fixture.debugElement.query(By.css('.toast-close-button'));
    closeButton.nativeElement.click();
    
    // Verify closeToast was called
    expect(component.closeToast).toHaveBeenCalled();
    
    // Verify toast is marked as removing
    expect(component.activeToasts[0].removing).toBeTruthy();
  });

  it('should automatically dismiss toast after its duration', fakeAsync(() => {
    // Create a spy for removeToast
    spyOn(component, 'removeToast').and.callThrough();
    
    // Create toast with 1 second duration
    toastService.showSuccess('Auto dismiss test', { duration: 1000 });
    fixture.detectChanges();
    
    // Verify toast is displayed
    expect(component.activeToasts.length).toBe(1);
    
    // Fast-forward time past duration
    tick(1100);
    
    // Fast-forward past animation delay
    tick(300);
    
    // Verify removeToast was called
    expect(component.removeToast).toHaveBeenCalled();
  }));

  it('should clear all toasts when clear action is received', () => {
    // Add multiple toasts
    toastService.showSuccess('Success message');
    toastService.showError('Error message');
    fixture.detectChanges();
    
    // Verify toasts are displayed
    expect(component.activeToasts.length).toBe(2);
    
    // Clear all toasts
    toastService.clear();
    fixture.detectChanges();
    
    // Verify toasts are being removed (marked with removing flag)
    expect(component.activeToasts.length).toBe(0);
  });

  it('should apply the correct positioning class', () => {
    // Create a toast to ensure container is rendered
    toastService.showSuccess('Test message');
    
    // Change position
    component.position = 'toast-bottom-left';
    fixture.detectChanges();
    
    // Verify container has the correct position class
    const container = fixture.debugElement.query(By.css('.toast-container'));
    expect(container.nativeElement.classList.contains('toast-bottom-left')).toBeTruthy();
  });

  it('should handle animation states correctly', () => {
    toastService.showSuccess('Animation test');
    fixture.detectChanges();
    
    // Get toast element and verify it's visible
    const toast = fixture.debugElement.query(By.css('.toast'));
    expect(toast.properties['@toastAnimation']).toBe('visible');
    
    // Close the toast
    component.closeToast(component.activeToasts[0]);
    fixture.detectChanges();
    
    // Verify animation state changed to removed
    expect(toast.properties['@toastAnimation']).toBe('removed');
  });

  it('should cleanup subscriptions on destroy', () => {
    // Create spy for unsubscribe
    const unsubscribeSpy = spyOn(component['subscription'], 'unsubscribe').and.callThrough();
    
    // Create spy for clearTimeouts
    const clearTimeoutsSpy = spyOn(component, 'clearTimeouts').and.callThrough();
    
    // Trigger component destruction
    component.ngOnDestroy();
    
    // Verify subscription was unsubscribed and timeouts cleared
    expect(unsubscribeSpy).toHaveBeenCalled();
    expect(clearTimeoutsSpy).toHaveBeenCalled();
  });

  it('should cancel timeout on manual close', fakeAsync(() => {
    // Create a toast with auto-dismiss
    toastService.showSuccess('Test timeout cancel');
    fixture.detectChanges();
    
    // Ensure timeoutRef is set
    expect(component.activeToasts[0].timeoutRef).toBeTruthy();
    
    // Store timeout reference
    const timeoutRef = component.activeToasts[0].timeoutRef;
    
    // Spy on clearTimeout
    spyOn(window, 'clearTimeout').and.callThrough();
    
    // Manually close toast
    component.closeToast(component.activeToasts[0]);
    
    // Verify clearTimeout was called with correct reference
    expect(window.clearTimeout).toHaveBeenCalledWith(timeoutRef);
    expect(component.activeToasts[0].timeoutRef).toBeNull();
  }));
});