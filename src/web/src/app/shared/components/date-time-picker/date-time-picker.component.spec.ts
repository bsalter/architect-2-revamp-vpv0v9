import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ChangeDetectorRef } from '@angular/core';
import { ReactiveFormsModule, FormControl, NgControl } from '@angular/forms';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';

import { DateTimePickerComponent } from './date-time-picker.component';
import { 
  formatDate, 
  parseStringToDate, 
  getCommonTimezones, 
  isValidTimezone 
} from '../../../core/utils/datetime-utils';
import { DateFormatPipe } from '../../pipes/date-format.pipe';
import { TimezonePipe } from '../../pipes/timezone.pipe';

describe('DateTimePickerComponent', () => {
  let component: DateTimePickerComponent;
  let fixture: ComponentFixture<DateTimePickerComponent>;
  
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [
        ReactiveFormsModule,
        BrowserAnimationsModule
      ],
      declarations: [
        DateTimePickerComponent,
        DateFormatPipe,
        TimezonePipe
      ],
      providers: [
        DateFormatPipe,
        TimezonePipe,
        ChangeDetectorRef
      ]
    }).compileComponents();
    
    fixture = TestBed.createComponent(DateTimePickerComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  // Component initialization tests
  describe('Initialization', () => {
    it('should initialize with default values', () => {
      expect(component.label).toBe('Date and Time');
      expect(component.placeholder).toBe('Select date and time');
      expect(component.required).toBe(false);
      expect(component.showTimezone).toBe(true);
      expect(component.disabled).toBe(false);
    });
    
    it('should initialize with custom input values', () => {
      component.label = 'Custom Label';
      component.placeholder = 'Custom Placeholder';
      component.required = true;
      component.timezone = 'America/New_York';
      component.showTimezone = false;
      component.disabled = true;
      
      component.ngOnInit();
      fixture.detectChanges();
      
      expect(component.label).toBe('Custom Label');
      expect(component.placeholder).toBe('Custom Placeholder');
      expect(component.required).toBe(true);
      expect(component.timezone).toBe('America/New_York');
      expect(component.showTimezone).toBe(false);
      expect(component.disabled).toBe(true);
    });
    
    it('should load available timezones on initialization', () => {
      expect(component.timezones.length).toBeGreaterThan(0);
      expect(component.timezones).toContain('UTC');
    });
    
    it('should set validators when required is true', () => {
      component.required = true;
      component.ngOnInit();
      
      expect(component.dateControl.validator).not.toBeNull();
      expect(component.timeControl.validator).not.toBeNull();
      if (component.showTimezone) {
        expect(component.timezoneControl.validator).not.toBeNull();
      }
    });
  });

  // ControlValueAccessor implementation tests
  describe('ControlValueAccessor implementation', () => {
    it('should write value to form controls', () => {
      const testDate = new Date(2023, 5, 15, 14, 30);
      spyOn(component.dateControl, 'setValue');
      spyOn(component.timeControl, 'setValue');
      
      component.writeValue(testDate);
      
      expect(component.value).toBe(testDate);
      expect(component.dateControl.setValue).toHaveBeenCalled();
      expect(component.timeControl.setValue).toHaveBeenCalled();
    });
    
    it('should handle null value in writeValue', () => {
      spyOn(component.dateControl, 'setValue');
      spyOn(component.timeControl, 'setValue');
      
      component.writeValue(null);
      
      expect(component.value).toBeNull();
      expect(component.dateControl.setValue).toHaveBeenCalledWith('', { emitEvent: false });
      expect(component.timeControl.setValue).toHaveBeenCalledWith('', { emitEvent: false });
    });
    
    it('should register onChange callback', () => {
      const onChangeSpy = jasmine.createSpy('onChange');
      component.registerOnChange(onChangeSpy);
      
      component.onChange(new Date());
      
      expect(onChangeSpy).toHaveBeenCalled();
    });
    
    it('should register onTouched callback', () => {
      const onTouchedSpy = jasmine.createSpy('onTouched');
      component.registerOnTouched(onTouchedSpy);
      
      component.onTouched();
      
      expect(onTouchedSpy).toHaveBeenCalled();
    });
    
    it('should enable/disable the component', () => {
      spyOn(component.dateControl, 'disable');
      spyOn(component.timeControl, 'disable');
      spyOn(component.timezoneControl, 'disable');
      spyOn(component.dateControl, 'enable');
      spyOn(component.timeControl, 'enable');
      spyOn(component.timezoneControl, 'enable');
      
      component.setDisabledState(true);
      
      expect(component.disabled).toBeTrue();
      expect(component.dateControl.disable).toHaveBeenCalled();
      expect(component.timeControl.disable).toHaveBeenCalled();
      expect(component.timezoneControl.disable).toHaveBeenCalled();
      
      component.setDisabledState(false);
      
      expect(component.disabled).toBeFalse();
      expect(component.dateControl.enable).toHaveBeenCalled();
      expect(component.timeControl.enable).toHaveBeenCalled();
      expect(component.timezoneControl.enable).toHaveBeenCalled();
    });
  });

  // Input handling tests
  describe('Input handling', () => {
    it('should update date on date input change', () => {
      const event = { target: { value: '2023-06-15' } } as unknown as Event;
      component.value = new Date(2023, 5, 10, 14, 30);
      
      spyOn<any>(component, 'updateValue');
      spyOn<any>(component, 'markAsTouched');
      
      component.onDateInputChange(event);
      
      expect(component['markAsTouched']).toHaveBeenCalled();
      expect(component['updateValue']).toHaveBeenCalled();
    });
    
    it('should update time on time input change', () => {
      const event = { target: { value: '16:45' } } as unknown as Event;
      component.value = new Date(2023, 5, 15, 14, 30);
      
      spyOn<any>(component, 'updateValue');
      spyOn<any>(component, 'markAsTouched');
      
      component.onTimeInputChange(event);
      
      expect(component['markAsTouched']).toHaveBeenCalled();
      expect(component['updateValue']).toHaveBeenCalled();
    });
    
    it('should handle time input with no existing date', () => {
      const event = { target: { value: '09:15' } } as unknown as Event;
      component.value = null;
      
      spyOn<any>(component, 'updateValue');
      
      component.onTimeInputChange(event);
      
      expect(component['updateValue']).toHaveBeenCalled();
    });
    
    it('should update timezone on timezone change', () => {
      spyOn(component.timezoneChange, 'emit');
      spyOn<any>(component, 'markAsTouched');
      
      component.onTimezoneChange('America/New_York');
      
      expect(component.timezone).toBe('America/New_York');
      expect(component.timezoneChange.emit).toHaveBeenCalledWith('America/New_York');
      expect(component['markAsTouched']).toHaveBeenCalled();
    });
  });

  // Validation tests
  describe('Validation', () => {
    it('should validate required fields', () => {
      component.required = true;
      component.ngOnInit();
      
      // Force controls to be invalid
      component.dateControl.setValue('');
      component.timeControl.setValue('');
      
      expect(component.isValidInput()).toBeFalse();
      
      // Make controls valid
      component.dateControl.setValue('2023-06-15');
      component.timeControl.setValue('14:30');
      if (component.showTimezone) {
        component.timezoneControl.setValue('UTC');
      }
      
      expect(component.isValidInput()).toBeTrue();
    });
    
    it('should validate min/max date constraints', () => {
      const testDate = new Date(2023, 5, 15);
      component.value = testDate;
      
      // No constraints
      expect(component.isValidInput()).toBeTrue();
      
      // Add min date constraint
      component.minDate = new Date(2023, 5, 20);
      expect(component.isValidInput()).toBeFalse();
      
      component.minDate = new Date(2023, 5, 10);
      expect(component.isValidInput()).toBeTrue();
      
      // Add max date constraint
      component.maxDate = new Date(2023, 5, 10);
      expect(component.isValidInput()).toBeFalse();
      
      component.maxDate = new Date(2023, 5, 20);
      expect(component.isValidInput()).toBeTrue();
    });
  });

  // Timezone formatting test
  describe('Timezone formatting', () => {
    it('should format timezone correctly', () => {
      const timezonePipeSpy = TestBed.inject(TimezonePipe);
      spyOn(timezonePipeSpy, 'transform').and.returnValue('ET -05:00');
      
      const result = component.getFormattedTimezone();
      
      expect(timezonePipeSpy.transform).toHaveBeenCalledWith(component.timezone, {
        includeOffset: true,
        includeAbbreviation: true
      });
      expect(result).toBe('ET -05:00');
    });
  });

  // Event emission tests
  describe('Event emission', () => {
    it('should emit dateChange event when value changes', () => {
      spyOn(component.dateChange, 'emit');
      
      const newDate = new Date(2023, 6, 15);
      component['updateValue'](newDate);
      
      expect(component.dateChange.emit).toHaveBeenCalledWith(newDate);
    });
    
    it('should emit timezoneChange event when timezone changes', () => {
      spyOn(component.timezoneChange, 'emit');
      
      component.onTimezoneChange('Europe/London');
      
      expect(component.timezoneChange.emit).toHaveBeenCalledWith('Europe/London');
    });
  });

  // Lifecycle hook tests
  describe('Lifecycle hooks', () => {
    it('should initialize display values in ngAfterViewInit', () => {
      const testDate = new Date(2023, 7, 20, 10, 30);
      component.value = testDate;
      
      spyOn<any>(component, 'formatDateForDisplay').and.returnValue({
        date: '2023-08-20',
        time: '10:30'
      });
      spyOn(component.dateControl, 'setValue');
      spyOn(component.timeControl, 'setValue');
      
      component.ngAfterViewInit();
      
      expect(component['formatDateForDisplay']).toHaveBeenCalledWith(testDate);
      expect(component.dateControl.setValue).toHaveBeenCalledWith('2023-08-20', { emitEvent: false });
      expect(component.timeControl.setValue).toHaveBeenCalledWith('10:30', { emitEvent: false });
    });
    
    it('should clean up in ngOnDestroy', () => {
      spyOn(component.destroy$, 'next');
      spyOn(component.destroy$, 'complete');
      
      component.ngOnDestroy();
      
      expect(component.destroy$.next).toHaveBeenCalled();
      expect(component.destroy$.complete).toHaveBeenCalled();
    });
  });
});