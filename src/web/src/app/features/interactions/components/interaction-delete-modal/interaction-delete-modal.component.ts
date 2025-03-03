import { Component, Input, Output, EventEmitter, OnInit, OnDestroy } from '@angular/core'; // @angular/core v16.2.0
import { Subject, Subscription } from 'rxjs'; // rxjs v7.8.1
import { takeUntil, finalize } from 'rxjs/operators'; // rxjs/operators v7.8.1

import { Interaction } from '../../models/interaction.model';
import { InteractionService } from '../../services/interaction.service';
import { ToastService } from '../../../../shared/services/toast.service';
import { formatInteractionDatetime } from '../../models/interaction.model';

/**
 * Component that displays a modal dialog for confirming and handling interaction deletion
 */
@Component({
  selector: 'app-interaction-delete-modal',
  templateUrl: './interaction-delete-modal.component.html',
  styleUrls: ['./interaction-delete-modal.component.scss']
})
export class InteractionDeleteModalComponent implements OnInit, OnDestroy {
  /** The interaction to be deleted */
  @Input() interaction: Interaction;
  
  /** Event emitted when an interaction is successfully deleted */
  @Output() deleted = new EventEmitter<void>();
  
  /** Event emitted when deletion is cancelled */
  @Output() cancel = new EventEmitter<void>();

  /** Subject used for cleaning up subscriptions */
  private destroy$ = new Subject<void>();
  
  /** Subscription to the loading state from InteractionService */
  private loadingSubscription: Subscription;
  
  /** Controls modal visibility */
  isVisible = false;
  
  /** Tracks if deletion is in progress */
  isDeleting = false;
  
  /** Formatted date string for display */
  formattedDate: string;

  /**
   * Initializes the component with required services
   * 
   * @param interactionService Service for deletion operations
   * @param toastService Service for success and error notifications
   */
  constructor(
    private interactionService: InteractionService,
    private toastService: ToastService
  ) {}

  /**
   * Lifecycle hook that initializes the component
   */
  ngOnInit(): void {
    // Subscribe to loading state from InteractionService
    this.loadingSubscription = this.interactionService.loading$
      .pipe(takeUntil(this.destroy$))
      .subscribe(isLoading => {
        this.isDeleting = isLoading;
      });
    
    // Format the interaction's datetime for display
    if (this.interaction && this.interaction.startDatetime) {
      this.formattedDate = formatInteractionDatetime(this.interaction.startDatetime);
    }
    
    this.isVisible = true;
  }

  /**
   * Lifecycle hook for cleanup when the component is destroyed
   */
  ngOnDestroy(): void {
    // Complete the destroy$ subject to unsubscribe from all observables
    this.destroy$.next();
    this.destroy$.complete();
    
    // Unsubscribe from loadingSubscription if it exists
    if (this.loadingSubscription) {
      this.loadingSubscription.unsubscribe();
    }
  }

  /**
   * Handler for delete confirmation from the user
   */
  onConfirmDelete(): void {
    if (!this.interaction || !this.interaction.id) {
      this.toastService.showError('Cannot delete: Invalid interaction data');
      return;
    }
    
    this.isDeleting = true;
    
    this.interactionService.deleteInteraction(this.interaction.id)
      .pipe(
        takeUntil(this.destroy$),
        finalize(() => {
          // The service handles setting loading state to false in its finalize block
        })
      )
      .subscribe({
        next: () => {
          this.toastService.showSuccess('Interaction deleted successfully');
          this.isVisible = false;
          this.deleted.emit();
        },
        error: (error) => {
          this.toastService.showError('Failed to delete interaction. Please try again.');
        }
      });
  }

  /**
   * Handler for canceling the delete operation
   */
  onCancel(): void {
    this.isVisible = false;
    this.cancel.emit();
  }

  /**
   * Generates the confirmation message with interaction details
   * 
   * @returns Formatted confirmation message
   */
  getConfirmationMessage(): string {
    if (!this.interaction) {
      return 'Are you sure you want to delete this interaction?';
    }
    
    let message = 'Are you sure you want to delete this interaction?\n\n';
    message += `Title: ${this.interaction.title}\n`;
    message += `Date: ${this.formattedDate}\n\n`;
    message += 'This action cannot be undone.';
    
    return message;
  }
}