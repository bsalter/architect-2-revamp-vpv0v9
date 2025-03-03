import { 
  Component, 
  Input, 
  Output, 
  EventEmitter, 
  OnInit, 
  OnDestroy, 
  HostListener, 
  ViewChild, 
  ElementRef, 
  AfterViewInit 
} from '@angular/core'; // @angular/core 16.2.0
import { Subject } from 'rxjs'; // rxjs 7.8.1
import { takeUntil } from 'rxjs/operators'; // rxjs 7.8.1
import { ClickOutsideDirective } from '../../directives/click-outside.directive';

/**
 * A reusable confirmation modal component that presents users with a
 * confirmation prompt before proceeding with potentially destructive
 * or important actions.
 * 
 * Features:
 * - Customizable title, message, and button text
 * - Support for custom button styling
 * - Click outside to dismiss (optional)
 * - Escape key to dismiss
 * - Processing state for async operations
 * - Fully accessible with keyboard navigation
 * 
 * Usage example:
 * ```html
 * <app-confirmation-modal
 *   #confirmModal
 *   title="Confirm Delete"
 *   message="Are you sure you want to delete this interaction? This action cannot be undone."
 *   confirmButtonText="Delete"
 *   (confirm)="onDeleteConfirmed()"
 *   (cancel)="onDeleteCancelled()">
 * </app-confirmation-modal>
 * ```
 * 
 * ```typescript
 * // In component
 * @ViewChild('confirmModal') confirmModal: ConfirmationModalComponent;
 * 
 * deleteInteraction() {
 *   this.confirmModal.show();
 * }
 * ```
 */
@Component({
  selector: 'app-confirmation-modal',
  templateUrl: './confirmation-modal.component.html',
  styleUrls: ['./confirmation-modal.component.scss']
})
export class ConfirmationModalComponent implements OnInit, AfterViewInit, OnDestroy {
  /**
   * Title of the confirmation modal
   */
  @Input() title = 'Confirm Action';
  
  /**
   * Message to display in the confirmation modal
   */
  @Input() message = 'Are you sure you want to proceed?';
  
  /**
   * Text for the confirm button
   */
  @Input() confirmButtonText = 'Confirm';
  
  /**
   * Text for the cancel button
   */
  @Input() cancelButtonText = 'Cancel';
  
  /**
   * CSS class to apply to the confirm button (can be used for different styles based on action type)
   */
  @Input() confirmButtonClass = 'btn-danger';
  
  /**
   * Whether to show a close icon in the top-right corner
   */
  @Input() showCloseIcon = true;
  
  /**
   * Whether to close the modal when clicking outside of it
   */
  @Input() closeOnClickOutside = true;
  
  /**
   * Whether the confirm action is currently processing (e.g., during API call)
   * When true, the confirm button will show a loading indicator and be disabled
   */
  @Input() processing = false;
  
  /**
   * Reference to the confirm button element for focusing
   */
  @ViewChild('confirmButton') confirmButtonRef: ElementRef;
  
  /**
   * Reference to the modal content for detecting outside clicks
   */
  @ViewChild('modalContent') modalContentRef: ElementRef;
  
  /**
   * Event emitted when the user confirms the action
   */
  @Output() confirm = new EventEmitter<void>();
  
  /**
   * Event emitted when the user cancels or dismisses the modal
   */
  @Output() cancel = new EventEmitter<void>();
  
  /**
   * Controls visibility of the modal
   */
  isVisible = false;
  
  /**
   * Subject used to clean up subscriptions when the component is destroyed
   */
  private destroy$ = new Subject<void>();
  
  /**
   * Initializes the confirmation modal component
   * 
   * @param elementRef Reference to the host element for DOM manipulation
   */
  constructor(private elementRef: ElementRef) {}
  
  /**
   * Angular lifecycle hook called after component initialization
   */
  ngOnInit(): void {
    // No initialization needed at this time
  }
  
  /**
   * Angular lifecycle hook called after view initialization
   * Sets up focus management for accessibility
   */
  ngAfterViewInit(): void {
    // Nothing to set up initially, focus handling is in show() method
  }
  
  /**
   * Angular lifecycle hook for cleanup when component is destroyed
   */
  ngOnDestroy(): void {
    // Complete the destroy subject to unsubscribe from any remaining subscriptions
    this.destroy$.next();
    this.destroy$.complete();
  }
  
  /**
   * Shows the confirmation modal
   * Sets focus to the confirm button for accessibility
   */
  show(): void {
    this.isVisible = true;
    
    // Prevent background scrolling while modal is open
    document.body.classList.add('modal-open');
    
    // Set focus to the confirm button after a brief delay to ensure the DOM is ready
    setTimeout(() => {
      if (this.confirmButtonRef && this.confirmButtonRef.nativeElement) {
        this.confirmButtonRef.nativeElement.focus();
      }
    }, 150);
  }
  
  /**
   * Hides the confirmation modal
   */
  hide(): void {
    this.isVisible = false;
    
    // Re-enable background scrolling
    document.body.classList.remove('modal-open');
  }
  
  /**
   * Handler for confirm button click
   * Emits the confirm event and hides the modal unless processing is true
   */
  onConfirm(): void {
    // Emit the confirm event to notify parent component
    this.confirm.emit();
    
    // Only hide the modal if we're not in a processing state
    // This allows the parent component to show a loading state while
    // performing an async operation
    if (!this.processing) {
      this.hide();
    }
  }
  
  /**
   * Handler for cancel button click
   * Hides the modal and emits the cancel event
   */
  onCancel(): void {
    this.hide();
    this.cancel.emit();
  }
  
  /**
   * Handles clicks outside the modal content
   * If closeOnClickOutside is true, closes the modal
   */
  handleClickOutside(): void {
    if (this.closeOnClickOutside) {
      this.onCancel();
    }
  }
  
  /**
   * Listens for keydown events to handle Escape key for accessibility
   * 
   * @param event The keyboard event
   */
  @HostListener('keydown', ['$event'])
  onKeyDown(event: KeyboardEvent): void {
    // Check if Escape key was pressed and modal is visible
    if (event.key === 'Escape' && this.isVisible) {
      this.onCancel();
    }
  }
  
  /**
   * Prevents click events from bubbling up to parent elements
   * Useful to prevent clicks on modal content from triggering handleClickOutside
   * 
   * @param event The mouse event
   */
  stopPropagation(event: Event): void {
    event.stopPropagation();
  }
}