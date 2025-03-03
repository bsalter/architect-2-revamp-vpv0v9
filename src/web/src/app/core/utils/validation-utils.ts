import { AbstractControl, ValidatorFn, ValidationErrors, FormGroup } from '@angular/forms'; // @angular/forms v16.2.0

/**
 * Regular expression pattern for validating email addresses
 */
export const EMAIL_PATTERN = '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$';

/**
 * Valid interaction types based on system requirements
 */
const VALID_INTERACTION_TYPES = ['Meeting', 'Call', 'Email', 'Other'];

/**
 * Checks if a value is empty (null, undefined, or empty string)
 * @param value The value to check
 * @returns True if the value is empty, false otherwise
 */
export function isEmptyValue(value: any): boolean {
  return value === null || value === undefined || (typeof value === 'string' && value.trim() === '');
}

/**
 * Custom required validator that handles various types of empty values
 * Improves on Angular's built-in required validator by checking for empty strings after trimming
 * @returns A validator function that returns an error object if validation fails
 */
export function required(): ValidatorFn {
  return (control: AbstractControl): ValidationErrors | null => {
    return isEmptyValue(control.value) ? { required: true } : null;
  };
}

/**
 * Validator for minimum string length
 * @param min The minimum required length
 * @returns A validator function that returns an error object if validation fails
 */
export function minLength(min: number): ValidatorFn {
  return (control: AbstractControl): ValidationErrors | null => {
    if (isEmptyValue(control.value)) {
      return null; // Don't validate empty values, let required validator handle those
    }
    
    const value = control.value as string;
    if (typeof value !== 'string') {
      return null; // Only validate strings
    }
    
    return value.length < min
      ? { minlength: { required: min, actual: value.length } }
      : null;
  };
}

/**
 * Validator for maximum string length
 * @param max The maximum allowed length
 * @returns A validator function that returns an error object if validation fails
 */
export function maxLength(max: number): ValidatorFn {
  return (control: AbstractControl): ValidationErrors | null => {
    if (isEmptyValue(control.value)) {
      return null; // Don't validate empty values
    }
    
    const value = control.value as string;
    if (typeof value !== 'string') {
      return null; // Only validate strings
    }
    
    return value.length > max
      ? { maxlength: { required: max, actual: value.length } }
      : null;
  };
}

/**
 * Validates that a value is a valid date
 * @returns A validator function that returns an error object if validation fails
 */
export function validDate(): ValidatorFn {
  return (control: AbstractControl): ValidationErrors | null => {
    if (isEmptyValue(control.value)) {
      return null; // Don't validate empty values
    }
    
    const date = new Date(control.value);
    // Check if date is valid (not NaN)
    return isNaN(date.getTime()) ? { invalidDate: true } : null;
  };
}

/**
 * Validates that a date comes after a reference date (typically for end date > start date)
 * @param controlNameToCompare The name of the control to compare with (containing the reference date)
 * @returns A validator function that returns an error object if validation fails
 */
export function dateAfter(controlNameToCompare: string): ValidatorFn {
  return (control: AbstractControl): ValidationErrors | null => {
    if (!(control.parent instanceof FormGroup)) {
      return null; // Can't compare if not in a FormGroup
    }
    
    const comparisonControl = control.parent.get(controlNameToCompare);
    
    // Don't validate if either control is missing or empty
    if (!comparisonControl || isEmptyValue(control.value) || isEmptyValue(comparisonControl.value)) {
      return null;
    }
    
    // Convert to Date objects for comparison
    const currentDate = new Date(control.value);
    const referenceDate = new Date(comparisonControl.value);
    
    // Check if both are valid dates first
    if (isNaN(currentDate.getTime()) || isNaN(referenceDate.getTime())) {
      return null; // Let validDate validator handle invalid dates
    }
    
    // Check if current date is after the reference date
    return currentDate <= referenceDate ? { dateRange: true } : null;
  };
}

/**
 * Validates email format using regex pattern
 * @returns A validator function that returns an error object if validation fails
 */
export function emailFormat(): ValidatorFn {
  return (control: AbstractControl): ValidationErrors | null => {
    if (isEmptyValue(control.value)) {
      return null; // Don't validate empty values
    }
    
    const pattern = new RegExp(EMAIL_PATTERN);
    const value = control.value as string;
    
    return pattern.test(value) ? null : { email: true };
  };
}

/**
 * Validates that the interaction type is one of the allowed values
 * @returns A validator function that returns an error object if validation fails
 */
export function interactionTypeValid(): ValidatorFn {
  return (control: AbstractControl): ValidationErrors | null => {
    if (isEmptyValue(control.value)) {
      return null; // Don't validate empty values
    }
    
    const value = control.value as string;
    return VALID_INTERACTION_TYPES.includes(value) ? null : { invalidInteractionType: true };
  };
}

/**
 * Combined validator for Interaction title (required, min 5, max 100 chars)
 * Combines multiple validators into a single function for convenience
 * @returns A validator function that returns an error object if validation fails
 */
export function titleValidator(): ValidatorFn {
  return (control: AbstractControl): ValidationErrors | null => {
    // Apply all validators in sequence
    const requiredError = required()(control);
    if (requiredError) {
      return requiredError;
    }
    
    const minLengthError = minLength(5)(control);
    if (minLengthError) {
      return minLengthError;
    }
    
    const maxLengthError = maxLength(100)(control);
    if (maxLengthError) {
      return maxLengthError;
    }
    
    return null;
  };
}

/**
 * Returns a user-friendly error message based on validation error type
 * @param errors The validation errors object from AbstractControl.errors
 * @param fieldName Optional field name to include in the error message
 * @returns A human-readable error message
 */
export function getValidationErrorMessage(errors: ValidationErrors | null, fieldName?: string): string {
  if (!errors) {
    return '';
  }
  
  // Format field name for display (capitalize first letter or use provided name)
  const displayName = fieldName || 'Field';
  
  // Check for different error types and return appropriate message
  if (errors.required) {
    return `${displayName} is required`;
  }
  
  if (errors.minlength) {
    return `${displayName} must be at least ${errors.minlength.required} characters`;
  }
  
  if (errors.maxlength) {
    return `${displayName} cannot exceed ${errors.maxlength.required} characters`;
  }
  
  if (errors.email) {
    return `Please enter a valid email address`;
  }
  
  if (errors.invalidDate) {
    return `Please enter a valid date for ${displayName}`;
  }
  
  if (errors.dateRange) {
    return `End date must be after start date`;
  }
  
  if (errors.invalidInteractionType) {
    return `Please select a valid interaction type`;
  }
  
  // Generic error message for unhandled validation errors
  return `${displayName} has an invalid value`;
}