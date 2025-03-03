import { Injectable } from '@angular/core'; // v16.2.0
import { FormBuilder, FormGroup, Validators, FormControl } from '@angular/forms'; // v16.2.0
import { Observable, of, BehaviorSubject, throwError } from 'rxjs'; // v7.8.1
import { catchError, tap, finalize, map } from 'rxjs/operators'; // v7.8.1

import { 
  Interaction, 
  InteractionCreate, 
  InteractionUpdate, 
  InteractionType, 
  INTERACTION_TYPE_OPTIONS 
} from '../models/interaction.model';
import { InteractionService } from './interaction.service';
import { SiteSelectionService } from '../../../core/auth/site-selection.service';
import { 
  formatDateTimeWithTimezone,
  isValidDateRange,
  parseStringToDate,
  isValidTimezone,
  getCommonTimezones,
  getCurrentTimezone
} from '../../../core/utils/datetime-utils';
import {
  required,
  minLength,
  maxLength,
  dateAfter,
  interactionTypeValid,
  titleValidator,
  getValidationErrorMessage
} from '../../../core/utils/validation-utils';
import {
  validateAllFormFields,
  getFormControlError,
  markFormGroupTouched,
  resetForm
} from '../../../core/utils/form-utils';

/**
 * Service that manages the Interaction form state, validation, and submission
 * Centralizes form business logic to ensure consistent validation and data handling
 * across create and edit operations.
 */
@Injectable({
  providedIn: 'root'
})
export class InteractionFormService {
  // BehaviorSubjects for loading and error states
  private loadingSubject = new BehaviorSubject<boolean>(false);
  public loading$ = this.loadingSubject.asObservable();
  
  private errorSubject = new BehaviorSubject<string | null>(null);
  public error$ = this.errorSubject.asObservable();
  
  // Form group for the interaction form
  public interactionForm: FormGroup;
  
  // Current interaction being edited (null for new interactions)
  private currentInteraction: Interaction | null = null;
  
  // Available timezones and interaction types for dropdowns
  private timezones: string[] = getCommonTimezones();
  private interactionTypes = INTERACTION_TYPE_OPTIONS;

  /**
   * Initializes the form service with required dependencies
   * 
   * @param fb FormBuilder for creating reactive forms
   * @param interactionService Service for interaction CRUD operations
   * @param siteService Service to get current site context
   */
  constructor(
    private fb: FormBuilder,
    private interactionService: InteractionService,
    private siteService: SiteSelectionService
  ) {
    // Initialize BehaviorSubjects
    this.loadingSubject = new BehaviorSubject<boolean>(false);
    this.loading$ = this.loadingSubject.asObservable();
    
    this.errorSubject = new BehaviorSubject<string | null>(null);
    this.error$ = this.errorSubject.asObservable();
    
    // Initialize form
    this.interactionForm = this.createInteractionForm();
  }

  /**
   * Creates a new reactive form with validation for interaction data
   * 
   * @returns A FormGroup configured with all interaction fields and validators
   */
  private createInteractionForm(): FormGroup {
    return this.fb.group({
      title: ['', [
        required(),
        minLength(5),
        maxLength(100)
      ]],
      type: ['', [
        required(),
        interactionTypeValid()
      ]],
      lead: ['', [
        required()
      ]],
      startDatetime: ['', [
        required()
      ]],
      endDatetime: ['', [
        required(),
        dateAfter('startDatetime')
      ]],
      timezone: [getCurrentTimezone(), [
        required(),
        (control: FormControl) => isValidTimezone(control.value) ? null : { invalidTimezone: true }
      ]],
      location: [''],
      description: ['', [
        required(),
        minLength(10)
      ]],
      notes: ['']
    });
  }

  /**
   * Resets and initializes the form for a new interaction
   * 
   * @returns The initialized form
   */
  public initializeForm(): FormGroup {
    resetForm(this.interactionForm);
    
    // Set default timezone
    this.interactionForm.get('timezone')?.setValue(getCurrentTimezone());
    
    // Clear current interaction reference
    this.currentInteraction = null;
    
    // Clear any error messages
    this.errorSubject.next(null);
    
    return this.interactionForm;
  }

  /**
   * Populates the form with an existing interaction's data for editing
   * 
   * @param interaction The interaction to edit
   * @returns The form patched with interaction data
   */
  public patchFormWithInteraction(interaction: Interaction): FormGroup {
    // Reset the form first
    resetForm(this.interactionForm);
    
    // Store the current interaction being edited
    this.currentInteraction = interaction;
    
    // Convert dates to the correct format for form inputs
    const formData = {
      ...interaction,
      startDatetime: interaction.startDatetime,
      endDatetime: interaction.endDatetime
    };
    
    // Patch the form with the interaction data
    this.interactionForm.patchValue(formData);
    
    return this.interactionForm;
  }

  /**
   * Validates the form and prepares data for submission
   * 
   * @returns Prepared data object or null if validation fails
   */
  private validateAndGetFormData(): InteractionCreate | InteractionUpdate | null {
    // Mark all fields as touched to trigger validation errors
    validateAllFormFields(this.interactionForm);
    
    // Check if form is valid
    if (!this.interactionForm.valid) {
      return null;
    }
    
    // Get form values
    const formValues = this.interactionForm.getRawValue();
    
    // Validate dates and timezone
    if (!isValidDateRange(formValues.startDatetime, formValues.endDatetime)) {
      this.interactionForm.get('endDatetime')?.setErrors({ dateRange: true });
      return null;
    }
    
    if (!isValidTimezone(formValues.timezone)) {
      this.interactionForm.get('timezone')?.setErrors({ invalidTimezone: true });
      return null;
    }
    
    // Return the validated form data
    return {
      title: formValues.title,
      type: formValues.type as InteractionType,
      lead: formValues.lead,
      startDatetime: formValues.startDatetime,
      endDatetime: formValues.endDatetime,
      timezone: formValues.timezone,
      location: formValues.location || '',
      description: formValues.description,
      notes: formValues.notes || ''
    };
  }

  /**
   * Submits the form data to create or update an interaction
   * 
   * @returns Observable that completes when the submission is processed
   */
  public submitForm(): Observable<Interaction> {
    // Set loading state
    this.loadingSubject.next(true);
    
    // Clear any previous error messages
    this.errorSubject.next(null);
    
    // Validate form and get data
    const formData = this.validateAndGetFormData();
    
    // If validation fails, handle error and return empty observable
    if (!formData) {
      this.loadingSubject.next(false);
      this.errorSubject.next('Please correct the validation errors before submitting.');
      return of(null as unknown as Interaction);
    }
    
    let request: Observable<Interaction>;
    
    // Determine if this is a create or update operation
    if (this.currentInteraction) {
      // Update existing interaction
      request = this.interactionService.updateInteraction(
        this.currentInteraction.id,
        formData as InteractionUpdate
      );
    } else {
      // Create new interaction
      const createData = formData as InteractionCreate;
      
      // Add site ID from the site service if not already set
      const currentSiteId = this.siteService.getCurrentSiteId();
      if (currentSiteId && !createData.siteId) {
        createData.siteId = currentSiteId;
      }
      
      request = this.interactionService.createInteraction(createData);
    }
    
    // Process the request with appropriate error handling
    return request.pipe(
      tap(() => {
        // Operation was successful
        const action = this.currentInteraction ? 'updated' : 'created';
        console.log(`Interaction ${action} successfully`);
      }),
      catchError(error => {
        // Handle error
        this.errorSubject.next(`Error ${this.currentInteraction ? 'updating' : 'creating'} interaction: ${error.message || 'Unknown error'}`);
        return throwError(() => error);
      }),
      finalize(() => {
        // Reset loading state when complete
        this.loadingSubject.next(false);
      })
    );
  }

  /**
   * Gets validation error messages for a specific form control
   * 
   * @param controlName The name of the form control
   * @returns Error message or empty string if no errors
   */
  public getFormErrors(controlName: string): string {
    const control = this.interactionForm.get(controlName);
    if (!control) {
      return '';
    }
    
    return getFormControlError(control);
  }

  /**
   * Checks if a form field is invalid and touched
   * 
   * @param controlName The name of the form control
   * @returns True if field is invalid and touched
   */
  public isFieldInvalid(controlName: string): boolean {
    const control = this.interactionForm.get(controlName);
    if (!control) {
      return false;
    }
    
    return control.invalid && control.touched;
  }

  /**
   * Gets the list of available interaction types for dropdowns
   * 
   * @returns Array of interaction type options with value and label
   */
  public getInteractionTypes(): any[] {
    return this.interactionTypes;
  }

  /**
   * Gets the list of available timezones for dropdowns
   * 
   * @returns Array of timezone identifiers
   */
  public getTimezones(): string[] {
    return this.timezones;
  }
  
  /**
   * Gets the loading state
   * 
   * @returns Observable of loading state
   */
  public isLoading(): Observable<boolean> {
    return this.loading$;
  }
  
  /**
   * Gets the current error message
   * 
   * @returns Observable of current error message
   */
  public getError(): Observable<string | null> {
    return this.error$;
  }
  
  /**
   * Sets an error message
   * 
   * @param errorMessage The error message to set
   */
  public setError(errorMessage: string): void {
    this.errorSubject.next(errorMessage);
  }
  
  /**
   * Clears the current error message
   */
  public clearError(): void {
    this.errorSubject.next(null);
  }
}