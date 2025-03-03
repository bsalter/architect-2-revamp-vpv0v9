import {
  Component,
  OnInit,
  Input,
  Output,
  EventEmitter,
  forwardRef,
  ViewChild,
  ElementRef,
  OnDestroy,
  AfterViewInit,
  ChangeDetectionStrategy,
  ChangeDetectorRef
} from '@angular/core'; // v16.2.0
import {
  ControlValueAccessor,
  NG_VALUE_ACCESSOR,
  FormControl,
  Validators
} from '@angular/forms'; // v16.2.0
import {
  Subject,
  takeUntil,
  debounceTime
} from 'rxjs'; // v7.8.1

import {
  formatDate,
  formatDateTimeWithTimezone,
  parseStringToDate,
  DATE_FORMATS,
  getCommonTimezones,
  isValidTimezone,
  isValidDateRange,
  getCurrentTimezone
} from '../../../core/utils/datetime-utils';
import { TimezonePipe } from '../../pipes/timezone.pipe';
import { DateFormatPipe } from '../../pipes/date-format.pipe';

/**
 * A reusable date and time picker component that implements ControlValueAccessor
 * for integration with Angular reactive forms, providing timezone-aware date/time
 * selection for Interaction records.
 */
@Component({
  selector: 'app-date-time-picker',
  templateUrl: './date-time-picker.component.html',
  styleUrls: ['./date-time-picker.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => DateTimePickerComponent),
      multi: true
    }
  ]
})
export class DateTimePickerComponent implements OnInit, AfterViewInit, OnDestroy, ControlValueAccessor {
  /** Label for the date-time picker */
  @Input() label = 'Date and Time';
  
  /** Placeholder text for the date input */
  @Input() placeholder = 'Select date and time';
  
  /** Whether the input is required */
  @Input() required = false;
  
  /** Current timezone identifier */
  @Input() timezone = '';
  
  /** Whether to show the timezone selector */
  @Input() showTimezone = true;
  
  /** Whether the component is disabled */
  @Input() disabled = false;
  
  /** Minimum allowed date */
  @Input() minDate: Date;
  
  /** Maximum allowed date */
  @Input() maxDate: Date;
  
  /** Emits when the date value changes */
  @Output() dateChange = new EventEmitter<Date>();
  
  /** Emits when the timezone changes */
  @Output() timezoneChange = new EventEmitter<string>();
  
  /** Reference to the date input element */
  @ViewChild('dateInput') dateInput: ElementRef;
  
  /** Reference to the time input element */
  @ViewChild('timeInput') timeInput: ElementRef;
  
  /** Subject for handling component destruction and unsubscribing */
  destroy$ = new Subject<void>();
  
  /** Form control for the date input */
  dateControl = new FormControl('');
  
  /** Form control for the time input */
  timeControl = new FormControl('');
  
  /** Form control for the timezone selector */
  timezoneControl = new FormControl('');
  
  /** List of available timezones */
  timezones: string[] = [];
  
  /** Current date value */
  value: Date;
  
  /** Function called when value changes (for ControlValueAccessor) */
  onChange = (_: any) => {};
  
  /** Function called when control is touched (for ControlValueAccessor) */
  onTouched = () => {};
  
  /** Whether the control has been touched */
  isTouched = false;
  
  /** Format for date input */
  dateInputFormat = DATE_FORMATS.INPUT_DATE;
  
  /** Format for time input */
  timeInputFormat = DATE_FORMATS.INPUT_TIME;

  /**
   * Creates an instance of DateTimePickerComponent.
   * 
   * @param timezonePipe - Pipe for formatting timezone display
   * @param dateFormatPipe - Pipe for formatting dates
   * @param cdr - Change detector reference for marking UI updates
   */
  constructor(
    private timezonePipe: TimezonePipe,
    private dateFormatPipe: DateFormatPipe,
    private cdr: ChangeDetectorRef
  ) {}

  /**
   * Initializes the component, loads timezone options, and sets up form controls
   */
  ngOnInit(): void {
    // Load available timezones
    this.timezones = getCommonTimezones();

    // Set default timezone if not specified
    if (!this.timezone) {
      this.timezone = getCurrentTimezone();
      this.timezoneChange.emit(this.timezone);
    }

    // Set validators based on required flag
    if (this.required) {
      this.dateControl.setValidators(Validators.required);
      this.timeControl.setValidators(Validators.required);
      if (this.showTimezone) {
        this.timezoneControl.setValidators(Validators.required);
      }
    }

    // Subscribe to date control changes
    this.dateControl.valueChanges
      .pipe(
        takeUntil(this.destroy$),
        debounceTime(300)
      )
      .subscribe(value => {
        if (this.dateControl.valid && value) {
          this.updateDateFromControls();
        }
      });

    // Subscribe to time control changes
    this.timeControl.valueChanges
      .pipe(
        takeUntil(this.destroy$),
        debounceTime(300)
      )
      .subscribe(value => {
        if (this.timeControl.valid && value) {
          this.updateDateFromControls();
        }
      });

    // Subscribe to timezone control changes
    if (this.showTimezone) {
      this.timezoneControl.valueChanges
        .pipe(
          takeUntil(this.destroy$),
          debounceTime(300)
        )
        .subscribe(timezone => {
          if (timezone && isValidTimezone(timezone)) {
            this.timezone = timezone;
            this.timezoneChange.emit(timezone);
            if (this.value) {
              const formatted = this.formatDateForDisplay(this.value);
              this.dateControl.setValue(formatted.date, { emitEvent: false });
              this.timeControl.setValue(formatted.time, { emitEvent: false });
            }
          }
        });
    }

    // Initialize timezone control with current value
    this.timezoneControl.setValue(this.timezone);

    // Set disabled state if needed
    if (this.disabled) {
      this.setDisabledState(true);
    }
  }

  /**
   * Lifecycle hook that runs after the component view is fully initialized
   */
  ngAfterViewInit(): void {
    // Initialize display values if we have a value
    if (this.value) {
      const formatted = this.formatDateForDisplay(this.value);
      this.dateControl.setValue(formatted.date, { emitEvent: false });
      this.timeControl.setValue(formatted.time, { emitEvent: false });
      this.cdr.markForCheck();
    }
  }

  /**
   * Lifecycle hook that cleans up subscriptions when component is destroyed
   */
  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * ControlValueAccessor method that writes a value to the component from the form model
   * 
   * @param date - Date value to write to the control
   */
  writeValue(date: Date): void {
    if (date instanceof Date && !isNaN(date.getTime())) {
      this.value = date;
      const formatted = this.formatDateForDisplay(date);
      this.dateControl.setValue(formatted.date, { emitEvent: false });
      this.timeControl.setValue(formatted.time, { emitEvent: false });
    } else {
      this.value = null;
      this.dateControl.setValue('', { emitEvent: false });
      this.timeControl.setValue('', { emitEvent: false });
    }
    this.cdr.markForCheck();
  }

  /**
   * ControlValueAccessor method that registers a callback function for change events
   * 
   * @param fn - Callback function to invoke when the value changes
   */
  registerOnChange(fn: Function): void {
    this.onChange = fn;
  }

  /**
   * ControlValueAccessor method that registers a callback function for blur/touched events
   * 
   * @param fn - Callback function to invoke when the control is touched
   */
  registerOnTouched(fn: Function): void {
    this.onTouched = fn;
  }

  /**
   * ControlValueAccessor method that enables/disables the component based on form state
   * 
   * @param isDisabled - Whether the control should be disabled
   */
  setDisabledState(isDisabled: boolean): void {
    this.disabled = isDisabled;
    if (isDisabled) {
      this.dateControl.disable();
      this.timeControl.disable();
      this.timezoneControl.disable();
    } else {
      this.dateControl.enable();
      this.timeControl.enable();
      this.timezoneControl.enable();
    }
    this.cdr.markForCheck();
  }

  /**
   * Handles changes to the date input field
   * 
   * @param event - The input event from the date field
   */
  onDateInputChange(event: Event): void {
    const input = event.target as HTMLInputElement;
    const dateValue = input.value;
    
    if (dateValue) {
      const date = parseStringToDate(dateValue, this.dateInputFormat);
      if (date && this.value) {
        // Preserve time from existing value
        date.setHours(this.value.getHours(), this.value.getMinutes(), this.value.getSeconds());
        this.updateValue(date);
      } else if (date) {
        // Default to midnight if no existing value
        date.setHours(0, 0, 0, 0);
        this.updateValue(date);
      }
    }
    
    this.markAsTouched();
  }

  /**
   * Handles changes to the time input field
   * 
   * @param event - The input event from the time field
   */
  onTimeInputChange(event: Event): void {
    const input = event.target as HTMLInputElement;
    const timeValue = input.value;
    
    if (timeValue) {
      // Extract hours and minutes from the time string
      const [hours, minutes] = timeValue.split(':').map(Number);
      
      if (this.value) {
        // Create a new date to avoid mutating the original
        const updatedDate = new Date(this.value);
        updatedDate.setHours(hours, minutes, 0, 0);
        this.updateValue(updatedDate);
      } else {
        // If no existing date, create a new date with the selected time
        const now = new Date();
        now.setHours(hours, minutes, 0, 0);
        this.updateValue(now);
      }
    }
    
    this.markAsTouched();
  }

  /**
   * Handles changes to the timezone selection
   * 
   * @param timezone - The selected timezone identifier
   */
  onTimezoneChange(timezone: string): void {
    if (isValidTimezone(timezone)) {
      this.timezone = timezone;
      this.timezoneChange.emit(timezone);
      
      // Update date formatting if a date is already selected
      if (this.value) {
        const formatted = this.formatDateForDisplay(this.value);
        this.dateControl.setValue(formatted.date, { emitEvent: false });
        this.timeControl.setValue(formatted.time, { emitEvent: false });
      }
    }
    
    this.markAsTouched();
  }

  /**
   * Updates the component value and notifies form of changes
   * 
   * @param newValue - The new date value
   */
  private updateValue(newValue: Date): void {
    if (newValue instanceof Date && !isNaN(newValue.getTime())) {
      this.value = newValue;
      this.onChange(newValue);
      this.dateChange.emit(newValue);
      
      // Update input display
      const formatted = this.formatDateForDisplay(newValue);
      this.dateControl.setValue(formatted.date, { emitEvent: false });
      this.timeControl.setValue(formatted.time, { emitEvent: false });
      
      this.cdr.markForCheck();
    }
  }

  /**
   * Marks the component as touched and notifies the form
   */
  private markAsTouched(): void {
    if (!this.isTouched) {
      this.isTouched = true;
      this.onTouched();
    }
  }

  /**
   * Formats the date for display in the input fields
   * 
   * @param date - The date to format
   * @returns Object with formatted date and time strings
   */
  private formatDateForDisplay(date: Date): { date: string; time: string } {
    if (!date || !(date instanceof Date) || isNaN(date.getTime())) {
      return { date: '', time: '' };
    }
    
    const formattedDate = formatDate(date, this.dateInputFormat);
    const formattedTime = formatDate(date, this.timeInputFormat);
    
    return { 
      date: formattedDate,
      time: formattedTime
    };
  }

  /**
   * Updates the date value based on the current form control values
   */
  private updateDateFromControls(): void {
    const dateValue = this.dateControl.value;
    const timeValue = this.timeControl.value;
    
    if (dateValue && timeValue) {
      // Parse date
      const date = parseStringToDate(dateValue, this.dateInputFormat);
      
      if (date) {
        // Parse time
        const [hours, minutes] = timeValue.split(':').map(Number);
        date.setHours(hours, minutes, 0, 0);
        
        // Update value
        this.updateValue(date);
      }
    }
  }

  /**
   * Validates the date/time input combinations
   * 
   * @returns True if the input combination is valid
   */
  isValidInput(): boolean {
    return (
      this.dateControl.valid &&
      this.timeControl.valid &&
      (!this.showTimezone || this.timezoneControl.valid) &&
      (!this.value || !this.minDate || this.value >= this.minDate) &&
      (!this.value || !this.maxDate || this.value <= this.maxDate)
    );
  }

  /**
   * Gets a formatted display string for the current timezone
   * 
   * @returns Formatted timezone display string
   */
  getFormattedTimezone(): string {
    return this.timezonePipe.transform(this.timezone, { 
      includeOffset: true,
      includeAbbreviation: true 
    });
  }
}