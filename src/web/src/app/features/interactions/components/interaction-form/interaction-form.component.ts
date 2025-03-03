import { Component, OnInit, OnDestroy, Input, Output, EventEmitter, ChangeDetectionStrategy, ChangeDetectorRef } from '@angular/core'; // v16.2.0
import { FormGroup } from '@angular/forms'; // v16.2.0
import { ActivatedRoute, Router } from '@angular/router'; // v16.2.0
import { Subscription, Observable, Subject, takeUntil } from 'rxjs'; // v7.8.1

import { 
  Interaction, 
  InteractionType, 
  INTERACTION_TYPE_OPTIONS 
} from '../../models/interaction.model';
import { InteractionFormService } from '../../services/interaction-form.service';
import { InteractionService } from '../../services/interaction.service';
import { ToastService } from '../../../shared/services/toast.service';
import { formatDateTimeWithTimezone } from '../../../core/utils/datetime-utils';

// Error messages for validation errors
const ERROR_MESSAGES = {
  required: 'This field is required',
  minlength: 'This field is too short',
  maxlength: 'This field is too long',
  dateafter: 'End date must be after start date'
};

/**
 * Component that provides a form interface for creating and editing interaction records
 * with validation, timezone support, and error handling. The component coordinates with
 * form services to handle data submission, validation, and state management.
 */
@Component({
  selector: 'app-interaction-form',
  templateUrl: './interaction-form.component.html',
  styleUrls: ['./interaction-form.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class InteractionFormComponent implements OnInit, OnDestroy {
  @Input() interaction: Interaction;
  @Input() isEditMode = false;
  @Output() formSubmitted = new EventEmitter<Interaction>();
  @Output() formCancelled = new EventEmitter<void>();

  private destroy$ = new Subject<void>();
  isLoading = false;
  form: FormGroup;
  formTitle: string;
  interactionTypes: any[];
  timezones: string[];
  private routeSubscription: Subscription;

  /**
   * Initializes the component with required dependencies
   * 
   * @param formService Service that manages form state, validation, and submission
   * @param interactionService Service for interaction CRUD operations
   * @param toastService Service for displaying success/error notifications
   * @param router Router for navigation after form submission
   * @param route ActivatedRoute for accessing route parameters
   * @param cdr ChangeDetectorRef for manual change detection triggering
   */
  constructor(
    private formService: InteractionFormService,
    private interactionService: InteractionService,
    private toastService: ToastService,
    private router: Router,
    private route: ActivatedRoute,
    private cdr: ChangeDetectorRef
  ) {
    // Initialize form from formService
    this.form = this.formService.interactionForm;
    this.interactionTypes = this.formService.getInteractionTypes();
    this.timezones = this.formService.getTimezones();
    
    // Subscribe to loading state changes
    this.formService.loading$.pipe(
      takeUntil(this.destroy$)
    ).subscribe(loading => {
      this.isLoading = loading;
      this.cdr.markForCheck();
    });
    
    // Initialize formTitle based on isEditMode
    this.formTitle = this.isEditMode ? 'Edit Interaction' : 'Create New Interaction';
  }

  /**
   * Lifecycle hook that initializes the component and loads data if in edit mode
   */
  ngOnInit(): void {
    // Subscribe to the route parameters
    this.routeSubscription = this.route.params.subscribe(params => {
      const interactionId = params['id'];
      
      // If interactionId is present in route params, load the interaction
      if (interactionId) {
        this.loadInteraction(+interactionId);
      } else if (this.isEditMode && this.interaction) {
        // If in edit mode but no interaction provided, fetch interaction by ID
        this.formService.patchFormWithInteraction(this.interaction);
      } else {
        // Otherwise initialize empty form for create mode
        this.formService.initializeForm();
      }
      
      // Set formTitle based on mode (Create or Edit)
      this.formTitle = this.isEditMode ? 'Edit Interaction' : 'Create New Interaction';
      this.cdr.markForCheck();
    });
  }

  /**
   * Lifecycle hook that cleans up subscriptions when component is destroyed
   */
  ngOnDestroy(): void {
    // Complete the destroy$ Subject to trigger takeUntil in observables
    this.destroy$.next();
    this.destroy$.complete();
    
    // Unsubscribe from routeSubscription
    if (this.routeSubscription) {
      this.routeSubscription.unsubscribe();
    }
  }

  /**
   * Loads an interaction by ID and populates the form
   * 
   * @param id Interaction ID to load
   */
  loadInteraction(id: number): void {
    this.interactionService.getInteraction(id)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (interaction) => {
          this.interaction = interaction;
          this.formService.patchFormWithInteraction(interaction);
          this.isEditMode = true;
          this.formTitle = 'Edit Interaction';
          this.cdr.markForCheck();
        },
        error: (error) => {
          this.toastService.showError('Failed to load interaction: ' + error.message);
          this.router.navigate(['/interactions']);
        }
      });
  }

  /**
   * Handles form submission for both create and edit operations
   */
  onSubmit(): void {
    this.formService.submitForm()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (interaction) => {
          if (interaction) {
            this.formSubmitted.emit(interaction);
            const actionText = this.isEditMode ? 'updated' : 'created';
            this.toastService.showSuccess(`Interaction successfully ${actionText}`);
            this.router.navigate(['/interactions']);
          }
        },
        error: (error) => {
          this.toastService.showError('Error saving interaction: ' + error.message);
        }
      });
  }

  /**
   * Handles cancellation of form editing
   */
  onCancel(): void {
    this.formCancelled.emit();
    this.router.navigate(['/interactions']);
  }

  /**
   * Resets the form to its initial state
   */
  resetForm(): void {
    this.formService.initializeForm();
    this.cdr.markForCheck();
  }

  /**
   * Checks if a form field is invalid and touched
   * 
   * @param controlName Name of the form control to check
   * @returns True if field is invalid and touched
   */
  isFieldInvalid(controlName: string): boolean {
    return this.formService.isFieldInvalid(controlName);
  }

  /**
   * Gets validation error message for a form field
   * 
   * @param controlName Name of the form control to get errors for
   * @returns Error message or empty string
   */
  getErrorMessage(controlName: string): string {
    return this.formService.getFormErrors(controlName);
  }

  /**
   * Formats a date/time for display with timezone consideration
   * 
   * @param date Date to format
   * @param timezone Timezone to format the date in
   * @returns Formatted date/time string
   */
  formatDateTime(date: Date, timezone: string): string {
    return formatDateTimeWithTimezone(date, 'MMM d, yyyy h:mm a', timezone);
  }
}