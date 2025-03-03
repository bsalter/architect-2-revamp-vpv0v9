import { Component, Input, OnInit } from '@angular/core'; // @angular/core version 16.2.0

/**
 * Component that displays standardized error messages throughout the application,
 * especially for form validation errors. Supports different error types with
 * appropriate styling and optional icons.
 * 
 * @example
 * <app-error-message
 *   message="Please enter a valid email address"
 *   type="validation"
 *   [showIcon]="true">
 * </app-error-message>
 */
@Component({
  selector: 'app-error-message',
  templateUrl: './error-message.component.html',
  styleUrls: ['./error-message.component.scss']
})
export class ErrorMessageComponent implements OnInit {
  /**
   * The error message text to display
   */
  @Input() message: string = '';

  /**
   * The type of error, which affects styling and icon
   * - 'validation': Form field validation errors (default)
   * - 'warning': Warning messages that require attention but don't prevent operation
   * - 'system': System or application errors
   */
  @Input() type: 'validation' | 'warning' | 'system' = 'validation';

  /**
   * Whether to show an icon alongside the error message
   */
  @Input() showIcon: boolean = true;

  // Valid error types for runtime checking
  private validTypes: ('validation' | 'warning' | 'system')[] = [
    'validation', 
    'warning', 
    'system'
  ];

  /**
   * Initializes the component with default values
   */
  constructor() {
    // Default values are set in property declarations
  }

  /**
   * Lifecycle hook that performs initialization after data-bound properties are set.
   * Validates inputs and ensures proper component configuration.
   */
  ngOnInit(): void {
    // Validate that message is provided
    if (!this.message) {
      console.warn('ErrorMessageComponent: No message provided');
    }

    // Ensure type is one of the valid options
    if (!this.validTypes.includes(this.type)) {
      console.warn(`ErrorMessageComponent: Invalid type '${this.type}', falling back to 'validation'`);
      this.type = 'validation';
    }

    // Ensure showIcon is properly initialized
    if (this.showIcon === undefined) {
      this.showIcon = true;
    }
  }
}