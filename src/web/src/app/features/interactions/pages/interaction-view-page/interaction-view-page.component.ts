import { Component, OnInit, OnDestroy, ViewChild } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Observable, Subject, Subscription } from 'rxjs';
import { takeUntil, switchMap, tap, catchError, finalize } from 'rxjs/operators';

import { Interaction } from '../../models/interaction.model';
import { InteractionService } from '../../services/interaction.service';
import { BreadcrumbService } from '../../../../shared/services/breadcrumb.service';
import { ToastService } from '../../../../shared/services/toast.service';
import { InteractionDeleteModalComponent } from '../../components/interaction-delete-modal/interaction-delete-modal.component';
import { formatInteractionDatetime, getDurationString } from '../../models/interaction.model';

/**
 * Component responsible for displaying detailed information about a specific interaction
 */
@Component({
  selector: 'app-interaction-view-page',
  templateUrl: './interaction-view-page.component.html',
  styleUrls: ['./interaction-view-page.component.scss']
})
export class InteractionViewPageComponent implements OnInit, OnDestroy {
  @ViewChild('deleteModal') deleteModal: InteractionDeleteModalComponent;
  
  private destroy$ = new Subject<void>();
  private loadingSubscription: Subscription;
  
  interaction: Interaction;
  loading = false;
  error = false;
  errorMessage = '';
  showDeleteModal = false;
  
  formattedStartDate: string;
  formattedEndDate: string;
  durationString: string;
  
  /**
   * Initializes the component with required services
   */
  constructor(
    private interactionService: InteractionService,
    private route: ActivatedRoute,
    private router: Router,
    private breadcrumbService: BreadcrumbService,
    private toastService: ToastService
  ) { }

  /**
   * Lifecycle hook that initializes the component
   */
  ngOnInit(): void {
    // Subscribe to loading state from interaction service
    this.loadingSubscription = this.interactionService.loading$
      .pipe(takeUntil(this.destroy$))
      .subscribe(loading => {
        this.loading = loading;
      });
    
    // Get the interaction ID from route parameters and load the interaction
    const id = +this.route.snapshot.paramMap.get('id');
    if (id) {
      this.loadInteraction(id);
    } else {
      this.error = true;
      this.errorMessage = 'Invalid interaction ID';
      this.toastService.showError('Invalid interaction ID');
    }
    
    // Subscribe to errors from interaction service
    this.interactionService.error$
      .pipe(takeUntil(this.destroy$))
      .subscribe(error => {
        if (error) {
          this.error = true;
          this.errorMessage = error.message || 'An error occurred while loading the interaction';
        }
      });
  }

  /**
   * Lifecycle hook for cleanup when component is destroyed
   */
  ngOnDestroy(): void {
    // Complete the destroy$ subject to unsubscribe from all observables
    this.destroy$.next();
    this.destroy$.complete();
    
    if (this.loadingSubscription) {
      this.loadingSubscription.unsubscribe();
    }
  }

  /**
   * Loads interaction data based on the provided ID
   */
  loadInteraction(id: number): void {
    this.error = false;
    this.errorMessage = '';
    
    this.interactionService.getInteraction(id)
      .pipe(takeUntil(this.destroy$))
      .subscribe(interaction => {
        if (interaction) {
          this.interaction = interaction;
          this.formatDates();
          
          // Update the breadcrumb with the interaction title
          this.breadcrumbService.updateLastBreadcrumb(this.interaction.title);
        }
      });
  }

  /**
   * Formats the date/time fields for display
   */
  formatDates(): void {
    if (this.interaction) {
      this.formattedStartDate = formatInteractionDatetime(this.interaction.startDatetime);
      this.formattedEndDate = formatInteractionDatetime(this.interaction.endDatetime);
      this.durationString = getDurationString(
        this.interaction.startDatetime, 
        this.interaction.endDatetime
      );
    }
  }

  /**
   * Navigates to edit page for the current interaction
   */
  onEdit(): void {
    this.router.navigate(['/interactions', this.interaction.id, 'edit']);
  }

  /**
   * Shows delete confirmation modal
   */
  onDelete(): void {
    this.showDeleteModal = true;
  }

  /**
   * Handles confirmed deletion from the modal
   */
  onDeleteConfirmed(): void {
    this.showDeleteModal = false;
    this.toastService.showSuccess('Interaction deleted successfully');
    this.router.navigate(['/interactions']);
  }

  /**
   * Handles canceled deletion from the modal
   */
  onDeleteCanceled(): void {
    this.showDeleteModal = false;
  }

  /**
   * Navigates back to the interactions list
   */
  onBack(): void {
    this.router.navigate(['/interactions']);
  }
}