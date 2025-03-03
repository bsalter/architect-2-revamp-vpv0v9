import { ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { DebugElement } from '@angular/core';

import { ConfirmationModalComponent } from './confirmation-modal.component';
import { LoadingIndicatorComponent } from '../loading-indicator/loading-indicator.component';

describe('ConfirmationModalComponent', () => {
  let component: ConfirmationModalComponent;
  let fixture: ComponentFixture<ConfirmationModalComponent>;
  let debugElement: DebugElement;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [
        ConfirmationModalComponent,
        LoadingIndicatorComponent
      ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(ConfirmationModalComponent);
    component = fixture.componentInstance;
    debugElement = fixture.debugElement;
    fixture.detectChanges();
  });

  it('should create the component', () => {
    expect(component).toBeTruthy();
  });

  it('should display the title in the modal header', () => {
    const testTitle = 'Test Title';
    component.title = testTitle;
    component.show();
    fixture.detectChanges();
    
    const titleElement = debugElement.query(By.css('.modal-title'));
    expect(titleElement.nativeElement.textContent).toContain(testTitle);
  });

  it('should display the message in the modal body', () => {
    const testMessage = 'Test confirmation message';
    component.message = testMessage;
    component.show();
    fixture.detectChanges();
    
    const messageElement = debugElement.query(By.css('.modal-body p'));
    expect(messageElement.nativeElement.textContent).toContain(testMessage);
  });

  it('should display default button texts when not specified', () => {
    component.show();
    fixture.detectChanges();
    
    const cancelButton = debugElement.query(By.css('.btn-secondary'));
    const confirmButton = debugElement.query(By.css(`.${component.confirmButtonClass}`));
    
    expect(cancelButton.nativeElement.textContent.trim()).toBe('Cancel');
    expect(confirmButton.nativeElement.textContent.trim()).toBe('Confirm');
  });

  it('should display custom button texts when specified', () => {
    component.confirmButtonText = 'Yes, Delete';
    component.cancelButtonText = 'No, Keep';
    component.show();
    fixture.detectChanges();
    
    const cancelButton = debugElement.query(By.css('.btn-secondary'));
    const confirmButton = debugElement.query(By.css(`.${component.confirmButtonClass}`));
    
    expect(cancelButton.nativeElement.textContent.trim()).toBe('No, Keep');
    expect(confirmButton.nativeElement.textContent.trim()).toBe('Yes, Delete');
  });

  it('should apply custom button class when specified', () => {
    component.confirmButtonClass = 'btn-warning';
    component.show();
    fixture.detectChanges();
    
    const confirmButton = debugElement.query(By.css('.btn-warning'));
    expect(confirmButton).toBeTruthy();
  });

  it('should emit confirm event when confirm button is clicked', () => {
    spyOn(component.confirm, 'emit');
    component.show();
    fixture.detectChanges();
    
    const confirmButton = debugElement.query(By.css(`.${component.confirmButtonClass}`));
    confirmButton.nativeElement.click();
    
    expect(component.confirm.emit).toHaveBeenCalled();
  });

  it('should emit cancel event when cancel button is clicked', () => {
    spyOn(component.cancel, 'emit');
    component.show();
    fixture.detectChanges();
    
    const cancelButton = debugElement.query(By.css('.btn-secondary'));
    cancelButton.nativeElement.click();
    
    expect(component.cancel.emit).toHaveBeenCalled();
  });

  it('should emit cancel event when backdrop is clicked', () => {
    spyOn(component.cancel, 'emit');
    component.closeOnClickOutside = true;
    component.show();
    fixture.detectChanges();
    
    // Simulate backdrop click through the handleClickOutside method
    component.handleClickOutside();
    
    expect(component.cancel.emit).toHaveBeenCalled();
  });

  it('should show loading indicator when processing is true', () => {
    component.processing = true;
    component.show();
    fixture.detectChanges();
    
    const loadingIndicator = debugElement.query(By.css('app-loading-indicator'));
    const confirmButton = debugElement.query(By.css(`.${component.confirmButtonClass}`));
    
    expect(loadingIndicator).toBeTruthy();
    expect(confirmButton.nativeElement.disabled).toBeTruthy();
  });

  it('should handle Escape key press to cancel the modal', () => {
    spyOn(component.cancel, 'emit');
    component.show();
    fixture.detectChanges();
    
    // Simulate Escape key press
    const event = new KeyboardEvent('keydown', { key: 'Escape' });
    component.onKeyDown(event);
    
    expect(component.cancel.emit).toHaveBeenCalled();
  });

  it('should not emit cancel on Escape key when processing', () => {
    spyOn(component.cancel, 'emit');
    component.processing = true;
    component.show();
    fixture.detectChanges();
    
    // Simulate Escape key press
    const event = new KeyboardEvent('keydown', { key: 'Escape' });
    component.onKeyDown(event);
    
    // When processing is true, cancel should not be called on Escape
    expect(component.cancel.emit).not.toHaveBeenCalled();
  });

  it('should set focus on confirm button after view initialization', () => {
    // Create spy on focus method
    const mockElement = { focus: jasmine.createSpy('focus') };
    component.confirmButtonRef = { nativeElement: mockElement } as any;
    
    // Use jasmine.clock to handle setTimeout
    jasmine.clock().install();
    
    // Show the modal
    component.show();
    
    // Advance the timer to trigger the setTimeout callback
    jasmine.clock().tick(200);
    
    // Verify focus was called on the button
    expect(mockElement.focus).toHaveBeenCalled();
    
    // Clean up
    jasmine.clock().uninstall();
  });

  it('should have proper accessibility attributes', () => {
    component.show();
    fixture.detectChanges();
    
    const modalElement = debugElement.query(By.css('.modal'));
    
    expect(modalElement.nativeElement.getAttribute('role')).toBe('dialog');
    expect(modalElement.nativeElement.getAttribute('aria-modal')).toBe('true');
    expect(modalElement.nativeElement.hasAttribute('aria-labelledby')).toBeTruthy();
    expect(modalElement.nativeElement.hasAttribute('aria-describedby')).toBeTruthy();
  });
});