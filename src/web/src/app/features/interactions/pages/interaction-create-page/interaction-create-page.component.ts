import { Component, OnInit, OnDestroy } from '@angular/core'; // v16.2.0
import { Router } from '@angular/router'; // v16.2.0
import { Subscription } from 'rxjs'; // v7.8.1
import { take, finalize } from 'rxjs/operators'; // v7.8.1

import { Interaction, InteractionCreate } from '../../models/interaction.model';
import { InteractionService } from '../../services/interaction.service';
import { InteractionFormService } from '../../services/interaction-form.service';
import { ToastService } from '../../../../shared/services/toast.service';
import { BreadcrumbService } from '../../../../shared/services/breadcrumb.service';
import { SiteSelectionService } from '../../../../core/auth/site-selection.service';

/**
 * Component that handles the creation of new interaction records.
 * Serves as a container for the interaction form component, managing the overall
 * creation workflow, form coordination, and success/error handling.
 */
@Component({
  selector: 'app-interaction-create-page',
  templateUrl: './interaction-create-page.component.html',
  styleUrls: ['./interaction-create-page.component.scss']
})
export class InteractionCreatePageComponent implements OnInit, OnDestroy {
  /** Flag indicating whether a data operation is in progress */
  isLoading = false;
  
  /** Flag indicating whether the form has validation errors */
  hasFormErrors = false;
  
  /** Collection of subscriptions to be cleaned up on component destruction */
  private subscriptions = new Subscription();

  /**
   * Creates an instance of the interaction creation page component
   * 
   * @param router Angular router for navigation
   * @param interactionService Service for interaction CRUD operations
   * @param formService Service for form state management
   * @param toastService Service for displaying notifications
   * @param breadcrumbService Service for managing breadcrumb navigation
   * @param siteService Service for site context management
   */
  constructor(
    private router: Router,
    private interactionService: InteractionService,
    private formService: InteractionFormService,
    private toastService: ToastService,
    private breadcrumbService: BreadcrumbService,
    private siteService: SiteSelectionService
  ) {
    // Track loading state from interaction service
    this.subscriptions.add(
      this.interactionService.loading$.subscribe(loading => {
        this.isLoading = loading;
      })
    );
  }

  /**
   * Lifecycle hook that initializes the component
   * Sets up breadcrumbs, initializes the form and subscribes to value changes
   */
  ngOnInit(): void {
    // Set breadcrumbs for navigation context
    this.breadcrumbService.setBreadcrumbs([
      { label: 'Dashboard', url: '/dashboard' },
      { label: 'Interactions', url: '/interactions' },
      { label: 'Create New', url: '/interactions/create' }
    ]);
    
    // Initialize a new interaction form
    this.formService.initializeForm();
    
    // Reset form error state when user makes changes to the form
    this.subscriptions.add(
      this.formService.interactionForm.valueChanges.subscribe(() => {
        if (this.hasFormErrors) {
          this.hasFormErrors = false;
        }
      })
    );
  }

  /**
   * Lifecycle hook that performs cleanup when component is destroyed
   */
  ngOnDestroy(): void {
    // Unsubscribe from all subscriptions to prevent memory leaks
    this.subscriptions.unsubscribe();
  }

  /**
   * Handles the form submission to create a new interaction
   */
  onSave(): void {
    // Validate the form data
    const formData = this.formService.validateAndGetFormData();
    
    // If validation fails, show errors and stop submission
    if (!formData) {
      this.hasFormErrors = true;
      return;
    }
    
    // Get current site ID from site context
    const siteId = this.siteService.getCurrentSiteId();
    
    // Ensure the interaction is associated with the current site
    if (siteId && !formData.siteId) {
      formData.siteId = siteId;
    }
    
    // Create the interaction via API
    this.interactionService.createInteraction(formData as InteractionCreate)
      .pipe(
        take(1), // Take only the first emission and complete
        finalize(() => this.isLoading = false) // Always reset loading state
      )
      .subscribe({
        next: (interaction: Interaction) => {
          // Show success message
          this.toastService.showSuccess('Interaction created successfully');
          // Navigate back to the finder page
          this.router.navigate(['/interactions']);
        },
        error: (error) => {
          // Show error message with details
          this.toastService.showError(
            `Failed to create interaction: ${error.message || 'Unknown error'}`
          );
        }
      });
  }

  /**
   * Handles cancellation of the creation process
   */
  onCancel(): void {
    // Navigate back to the interactions finder page
    this.router.navigate(['/interactions']);
  }

  /**
   * Navigates back to the interactions finder page
   */
  goBack(): void {
    this.router.navigate(['/interactions']);
  }
}