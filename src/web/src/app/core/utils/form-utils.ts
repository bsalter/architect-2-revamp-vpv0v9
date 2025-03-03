/**
 * Form utilities module
 * 
 * This module provides utility functions for Angular reactive forms management,
 * validation, and error handling throughout the Interaction Management System.
 * 
 * @version 1.0.0
 */

import { 
  FormGroup, 
  FormControl, 
  FormArray, 
  AbstractControl, 
  ValidationErrors, 
  ValidatorFn 
} from '@angular/forms'; // v16.2.0
import { isEmpty, isNotEmpty } from './string-utils';

/**
 * Default validation error messages used throughout the application
 */
export const DEFAULT_ERROR_MESSAGES = {
  required: 'This field is required',
  email: 'Please enter a valid email address',
  minlength: 'This field is too short',
  maxlength: 'This field is too long',
  pattern: 'The format is invalid',
  invalidDate: 'Please enter a valid date',
  dateRange: 'End date must be after start date',
  invalidTimezone: 'Please select a valid timezone',
  invalidInteractionType: 'Please select a valid interaction type'
};

/**
 * Recursively marks all controls in a form group as touched
 * to trigger validation visual feedback
 * 
 * @param formGroup - The form group containing controls to mark as touched
 */
export function markFormGroupTouched(formGroup: FormGroup): void {
  Object.keys(formGroup.controls).forEach(key => {
    const control = formGroup.controls[key];
    
    if (control instanceof FormControl) {
      control.markAsTouched({ onlySelf: true });
    } else if (control instanceof FormGroup) {
      markFormGroupTouched(control);
    } else if (control instanceof FormArray) {
      for (let i = 0; i < control.length; i++) {
        if (control.at(i) instanceof FormGroup) {
          markFormGroupTouched(control.at(i) as FormGroup);
        } else {
          (control.at(i) as FormControl).markAsTouched({ onlySelf: true });
        }
      }
    }
  });
}

/**
 * Validates all fields in a form group and marks them as touched
 * to trigger error display
 * 
 * @param formGroup - The form group to validate
 * @returns True if the form is valid, false otherwise
 */
export function validateAllFormFields(formGroup: FormGroup): boolean {
  markFormGroupTouched(formGroup);
  return formGroup.valid;
}

/**
 * Resets a form group to its initial state or to provided values
 * 
 * @param formGroup - The form group to reset
 * @param values - Optional values to set after reset
 */
export function resetForm(formGroup: FormGroup, values?: object): void {
  if (!formGroup) return;
  
  formGroup.reset(values || {});
  formGroup.markAsPristine();
  formGroup.markAsUntouched();
}

/**
 * Checks if a form control has a specific error
 * 
 * @param control - The control to check for errors
 * @param errorType - The specific error type to check for
 * @returns True if the control has the specified error
 */
export function hasFormError(control: AbstractControl, errorType: string): boolean {
  if (!control || !control.errors) {
    return false;
  }
  
  return control.errors[errorType] !== undefined;
}

/**
 * Gets an appropriate error message for a form control based on its validation errors
 * 
 * @param control - The control to get errors for
 * @param customErrorMessages - Optional custom error messages to override defaults
 * @returns Error message or empty string if no errors
 */
export function getFormControlError(
  control: AbstractControl, 
  customErrorMessages?: { [key: string]: string }
): string {
  if (!control || !control.errors || !control.touched) {
    return '';
  }
  
  const errorMessages = { ...DEFAULT_ERROR_MESSAGES, ...customErrorMessages };
  const errorKeys = Object.keys(control.errors);
  
  if (errorKeys.length === 0) {
    return '';
  }
  
  const errorKey = errorKeys[0];
  const error = control.errors[errorKey];
  
  // Handle special cases for errors that include requirements
  if (errorKey === 'minlength') {
    return `Must be at least ${error.requiredLength} characters`;
  } else if (errorKey === 'maxlength') {
    return `Cannot exceed ${error.requiredLength} characters`;
  } else if (errorMessages[errorKey]) {
    return errorMessages[errorKey];
  }
  
  return 'Invalid value';
}

/**
 * Collects all validation errors from a form group
 * 
 * @param formGroup - The form group to collect errors from
 * @returns Object containing all form errors organized by control name
 */
export function getFormValidationErrors(formGroup: FormGroup): { [key: string]: any } {
  const errors: { [key: string]: any } = {};
  
  if (!formGroup) {
    return errors;
  }
  
  Object.keys(formGroup.controls).forEach(key => {
    const control = formGroup.get(key);
    
    if (!control) {
      return;
    }
    
    if (control.errors && Object.keys(control.errors).length > 0 && control.touched) {
      errors[key] = control.errors;
    }
    
    if (control instanceof FormGroup) {
      const nestedErrors = getFormValidationErrors(control);
      if (Object.keys(nestedErrors).length > 0) {
        errors[key] = nestedErrors;
      }
    }
    
    if (control instanceof FormArray) {
      const arrayErrors: any[] = [];
      let hasErrors = false;
      
      control.controls.forEach((arrayControl, index) => {
        if (arrayControl instanceof FormGroup) {
          const nestedErrors = getFormValidationErrors(arrayControl);
          if (Object.keys(nestedErrors).length > 0) {
            arrayErrors[index] = nestedErrors;
            hasErrors = true;
          }
        } else if (arrayControl.errors && arrayControl.touched) {
          arrayErrors[index] = arrayControl.errors;
          hasErrors = true;
        }
      });
      
      if (hasErrors) {
        errors[key] = arrayErrors;
      }
    }
  });
  
  return errors;
}

/**
 * Converts an object to FormData, useful for file uploads
 * 
 * @param data - The object to convert to FormData
 * @returns FormData object with all values from the input object
 */
export function createFormData(data: { [key: string]: any }): FormData {
  const formData = new FormData();
  
  if (!data) {
    return formData;
  }
  
  const buildFormData = (formData: FormData, data: any, parentKey?: string) => {
    if (data && typeof data === 'object' && !(data instanceof Date) && !(data instanceof File) && !(data instanceof Blob)) {
      Object.keys(data).forEach(key => {
        const value = data[key];
        const formKey = parentKey ? `${parentKey}[${key}]` : key;
        
        if (value instanceof Date) {
          formData.append(formKey, value.toISOString());
        } else if (value instanceof File) {
          formData.append(formKey, value, value.name);
        } else if (value instanceof Blob) {
          formData.append(formKey, value);
        } else if (Array.isArray(value)) {
          value.forEach((item, index) => {
            const arrayKey = `${formKey}[${index}]`;
            if (item instanceof File) {
              formData.append(arrayKey, item, item.name);
            } else if (item instanceof Blob) {
              formData.append(arrayKey, item);
            } else if (item instanceof Date) {
              formData.append(arrayKey, item.toISOString());
            } else if (typeof item === 'object' && item !== null) {
              buildFormData(formData, item, arrayKey);
            } else if (item !== null && item !== undefined) {
              formData.append(arrayKey, item.toString());
            }
          });
        } else if (value !== null && value !== undefined) {
          formData.append(formKey, typeof value === 'object' ? JSON.stringify(value) : value.toString());
        }
      });
    } else if (data !== null && data !== undefined && parentKey) {
      if (data instanceof Date) {
        formData.append(parentKey, data.toISOString());
      } else if (data instanceof File) {
        formData.append(parentKey, data, data.name);
      } else if (data instanceof Blob) {
        formData.append(parentKey, data);
      } else {
        formData.append(parentKey, data.toString());
      }
    }
  };
  
  buildFormData(formData, data);
  return formData;
}

/**
 * Safely patches a form with values, handling missing or null properties
 * 
 * @param form - The form to patch
 * @param values - The values to patch
 */
export function patchFormValues(form: FormGroup, values: { [key: string]: any }): void {
  if (!form || !values) {
    return;
  }
  
  // Filter out undefined or null values to prevent overwriting with null
  const filteredValues: { [key: string]: any } = {};
  Object.keys(values).forEach(key => {
    if (values[key] !== undefined && values[key] !== null) {
      filteredValues[key] = values[key];
    }
  });
  
  form.patchValue(filteredValues, { emitEvent: false });
}

/**
 * Compares current form values with original values to detect changes
 * 
 * @param originalValues - The original values to compare against
 * @param currentValues - The current values to compare
 * @returns True if values have changed, false if they are the same
 */
export function compareFormValues(
  originalValues: { [key: string]: any }, 
  currentValues: { [key: string]: any }
): boolean {
  if (!originalValues || !currentValues) {
    return false;
  }
  
  const deepCompare = (obj1: any, obj2: any, ignoreKeys: string[] = []): boolean => {
    // If either is null/undefined, check for equality
    if (obj1 === null || obj1 === undefined || obj2 === null || obj2 === undefined) {
      return obj1 === obj2;
    }
    
    // Special case for dates
    if (obj1 instanceof Date && obj2 instanceof Date) {
      return obj1.getTime() === obj2.getTime();
    }
    
    // If types don't match, they're different
    if (typeof obj1 !== typeof obj2) {
      return false;
    }
    
    // If they're not objects, do simple comparison
    if (typeof obj1 !== 'object') {
      return obj1 === obj2;
    }
    
    // Handle arrays
    if (Array.isArray(obj1) && Array.isArray(obj2)) {
      if (obj1.length !== obj2.length) {
        return false;
      }
      
      for (let i = 0; i < obj1.length; i++) {
        if (!deepCompare(obj1[i], obj2[i], ignoreKeys)) {
          return false;
        }
      }
      
      return true;
    }
    
    // Compare object keys, ignoring specified keys
    const keys1 = Object.keys(obj1).filter(key => !ignoreKeys.includes(key));
    const keys2 = Object.keys(obj2).filter(key => !ignoreKeys.includes(key));
    
    if (keys1.length !== keys2.length) {
      return false;
    }
    
    return !keys1.some(key => {
      // Skip ignored keys
      if (ignoreKeys.includes(key)) {
        return false;
      }
      
      // If key doesn't exist in obj2, objects are different
      if (!Object.prototype.hasOwnProperty.call(obj2, key)) {
        return true;
      }
      
      // Recursively compare nested objects
      return !deepCompare(obj1[key], obj2[key], ignoreKeys);
    });
  };
  
  // Ignore metadata fields when comparing
  const ignoreKeys = ['id', 'created_at', 'updated_at', 'created_by'];
  return !deepCompare(originalValues, currentValues, ignoreKeys);
}

/**
 * Checks if a form has been modified by comparing to original values
 * 
 * @param form - The form to check
 * @param originalValues - The original values to compare against
 * @returns True if form has been modified
 */
export function isDirty(form: FormGroup, originalValues: { [key: string]: any }): boolean {
  if (!form || !originalValues) {
    return false;
  }
  
  const currentValues = form.getRawValue();
  return compareFormValues(originalValues, currentValues);
}

/**
 * Gets a list of field names that have been touched in a form
 * 
 * @param form - The form to extract touched fields from
 * @returns Array of touched field names
 */
export function extractTouchedFields(form: FormGroup): string[] {
  const touchedFields: string[] = [];
  
  if (!form) {
    return touchedFields;
  }
  
  const extractFields = (form: FormGroup, prefix = ''): void => {
    Object.keys(form.controls).forEach(key => {
      const control = form.get(key);
      const fullPath = prefix ? `${prefix}.${key}` : key;
      
      if (!control) {
        return;
      }
      
      if (control.touched) {
        touchedFields.push(fullPath);
      }
      
      if (control instanceof FormGroup) {
        extractFields(control, fullPath);
      }
      
      if (control instanceof FormArray) {
        control.controls.forEach((arrayControl, index) => {
          const arrayPath = `${fullPath}[${index}]`;
          
          if (arrayControl.touched) {
            touchedFields.push(arrayPath);
          }
          
          if (arrayControl instanceof FormGroup) {
            extractFields(arrayControl as FormGroup, arrayPath);
          }
        });
      }
    });
  };
  
  extractFields(form);
  return touchedFields;
}