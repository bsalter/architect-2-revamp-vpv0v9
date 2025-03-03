import { ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { AlertComponent } from './alert.component';

describe('AlertComponent', () => {
  let component: AlertComponent;
  let fixture: ComponentFixture<AlertComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [AlertComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(AlertComponent);
    component = fixture.componentInstance;
    component.message = 'Test alert message';
    fixture.detectChanges();
  });

  it('should create the component', () => {
    expect(component).toBeTruthy();
  });

  it("should have default type set to 'info'", () => {
    expect(component.type).toBe('info');
  });

  it('should set message correctly', () => {
    const testMessage = 'Test alert message';
    component.message = testMessage;
    fixture.detectChanges();
    
    const alertElement = fixture.debugElement.query(By.css('.alert'));
    expect(alertElement.nativeElement.textContent).toContain(testMessage);
  });

  it('should set type class correctly', () => {
    const types = ['success', 'warning', 'danger', 'info'];
    
    types.forEach(type => {
      component.type = type;
      fixture.detectChanges();
      
      const alertElement = fixture.debugElement.query(By.css(`.alert-${type}`));
      expect(alertElement).toBeTruthy();
    });
  });

  it('should display correct icon based on type', () => {
    const typeIconMap = {
      'success': 'check-circle',
      'warning': 'exclamation-triangle',
      'danger': 'exclamation-circle',
      'info': 'info-circle'
    };
    
    Object.entries(typeIconMap).forEach(([type, iconName]) => {
      component.type = type;
      fixture.detectChanges();
      
      const iconElement = fixture.debugElement.query(By.css(`.fa-${iconName}`));
      expect(iconElement).toBeTruthy();
    });
  });

  it('should show close button when dismissible is true', () => {
    component.dismissible = true;
    fixture.detectChanges();
    
    const closeButton = fixture.debugElement.query(By.css('.alert-close'));
    expect(closeButton).toBeTruthy();
  });

  it('should hide close button when dismissible is false', () => {
    component.dismissible = false;
    fixture.detectChanges();
    
    const closeButton = fixture.debugElement.query(By.css('.alert-close'));
    expect(closeButton).toBeFalsy();
  });

  it('should emit closed event when close button is clicked', () => {
    spyOn(component.closed, 'emit');
    spyOn(component, 'closeAlert').and.callThrough();
    component.dismissible = true;
    fixture.detectChanges();
    
    const closeButton = fixture.debugElement.query(By.css('.alert-close'));
    closeButton.nativeElement.click();
    
    expect(component.closeAlert).toHaveBeenCalled();
    expect(component.closed.emit).toHaveBeenCalled();
  });

  it('should not display when message is empty', () => {
    component.message = '';
    fixture.detectChanges();
    
    const alertElement = fixture.debugElement.query(By.css('.alert'));
    expect(alertElement).toBeFalsy();
  });
});