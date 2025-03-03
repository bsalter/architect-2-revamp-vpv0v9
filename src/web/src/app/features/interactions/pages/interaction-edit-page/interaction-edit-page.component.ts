import { Component, OnInit, OnDestroy } from '@angular/core'; // @angular/core v16.2.0
import { ActivatedRoute, Router } from '@angular/router'; // @angular/router v16.2.0
import { Subject, Observable, takeUntil } from 'rxjs'; // rxjs v7.8.1

import { Interaction } from '../../models/interaction.model';
import { InteractionService } from '../../services/interaction.service';
import { InteractionFormComponent } from '../../components/interaction-form/interaction-form.component';
import { ToastService } from '../../../shared/services/toast.service';
import { BreadcrumbService } from '../../../shared/services/breadcrumb.service';

/**
 * Component that manages the interaction edit page, loading interaction data and coordinating with the form component
 */
@Component({
  selector: 'app-interaction-edit-page',
  templateUrl: './interaction-edit-page.component.html',
  styleUrls: ['./interaction-edit-page.component.scss']
})
export class InteractionEditPageComponent implements OnInit, OnDestroy {
  interaction: Interaction;
  isLoading = false;
  errorMessage: string;
  private destroy$ = new Subject<void>();

  /**
   * Initializes the component with required dependencies
   */
  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private interactionService: InteractionService,
    private toastService: ToastService,
    private breadcrumbService: BreadcrumbService
  ) {
    // Subscribe to loading state from interactionService
    this.interactionService.loading$.pipe(
      takeUntil(this.destroy$)
    ).subscribe(loading => {
      this.isLoading = loading;
    });

    // Subscribe to error state from interactionService
    this.interactionService.error$.pipe(
      takeUntil(this.destroy$)
    ).subscribe(error => {
      this.errorMessage = error ? error.message || 'An error occurred' : null;
    });
  }

  /**
   * Lifecycle hook that initializes the component and loads interaction data
   */
  ngOnInit(): void {
    // Extract interactionId from route parameters
    this.route.params.pipe(
      takeUntil(this.destroy$)
    ).subscribe(params => {
      const interactionId = params['id'];
      if (interactionId) {
        this.loadInteraction(+interactionId);
      } else {
        this.toastService.showError('No interaction ID provided');
        this.navigateBack();
      }
    });

    // Setup breadcrumbs for navigation
    this.breadcrumbService.setBreadcrumbs([
      { label: 'Interactions', url: '/interactions' },
      { label: 'Edit Interaction', url: '' }
    ]);
  }

  /**
   * Lifecycle hook that cleans up subscriptions when component is destroyed
   */
  ngOnDestroy(): void {
    // Complete the destroy$ Subject to trigger takeUntil in observables
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * Loads interaction data from the service by ID
   * 
   * @param id The interaction ID to load
   */
  loadInteraction(id: number): void {
    this.interactionService.getInteraction(id)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (interaction) => {
          this.interaction = interaction;
          // Update breadcrumbs with interaction title
          this.breadcrumbService.setBreadcrumbs([
            { label: 'Interactions', url: '/interactions' },
            { label: `Edit: ${interaction.title}`, url: '' }
          ]);
        },
        error: (error) => {
          this.toastService.showError('Failed to load interaction: ' + error.message);
          this.navigateBack();
        }
      });
  }

  /**
   * Handles successful form submission
   * 
   * @param updatedInteraction The updated interaction data
   */
  handleFormSubmitted(updatedInteraction: Interaction): void {
    this.toastService.showSuccess('Interaction updated successfully');
    this.navigateBack();
  }

  /**
   * Handles form cancellation
   */
  handleFormCancelled(): void {
    this.navigateBack();
  }

  /**
   * Navigates back to the interaction detail view
   */
  navigateBack(): void {
    // Navigate to interaction detail route using router
    if (this.interaction) {
      this.router.navigate(['/interactions', this.interaction.id]);
    } else {
      this.router.navigate(['/interactions']);
    }
  }
}