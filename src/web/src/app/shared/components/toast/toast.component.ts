import { Component, OnInit, OnDestroy } from '@angular/core'; // @angular/core v16.2.0
import { trigger, state, style, transition, animate } from '@angular/animations'; // @angular/animations v16.2.0
import { Subscription } from 'rxjs'; // rxjs v7.8.1
import { ToastService } from '@app/core'; // @app/core v1.0.0

// Interface for toast message structure
// This interface represents the structure of toast notifications used throughout the application
interface ToastMessage {
  type: string;
  message: string;
  title: string;
  duration: number;
  timestamp: number;
  isCloseAction?: boolean;
  removing?: boolean;
  timeoutRef?: any;
}

/**
 * Animation trigger for toast notifications entry and exit
 * Provides smooth visual transitions when toasts appear and disappear
 */
export const toastAnimation = trigger('toastAnimation', [
  state('void', style({
    transform: 'translateX(100%)',
    opacity: 0
  })),
  state('visible', style({
    transform: 'translateX(0)',
    opacity: 1
  })),
  state('removed', style({
    transform: 'translateX(100%)',
    opacity: 0
  })),
  transition('void => visible', animate('300ms ease-out')),
  transition('visible => removed', animate('300ms ease-in'))
]);

/**
 * Component that displays toast notifications in the application
 * Provides temporary, non-intrusive messages with different styling based on type
 */
@Component({
  selector: 'app-toast',
  templateUrl: './toast.component.html',
  styleUrls: ['./toast.component.scss'],
  animations: [toastAnimation]
})
export class ToastComponent implements OnInit, OnDestroy {
  // Where toasts appear, default is top-right corner
  position = 'toast-top-right';
  
  // Array of active toast notifications
  activeToasts: ToastMessage[] = [];
  
  // Subscription for toast service messages
  private subscription = new Subscription();

  /**
   * Initializes the component with the ToastService
   */
  constructor(private toastService: ToastService) { }

  /**
   * Lifecycle hook that subscribes to toast messages
   */
  ngOnInit(): void {
    this.subscription.add(
      this.toastService.getToasts().subscribe(toasts => {
        this.processToasts(toasts);
      })
    );
  }

  /**
   * Lifecycle hook to clean up resources
   */
  ngOnDestroy(): void {
    this.subscription.unsubscribe();
    this.clearTimeouts();
  }

  /**
   * Processes toast messages and sets up auto-dismiss
   * @param toasts Array of toast messages to process
   */
  processToasts(toasts: ToastMessage[]): void {
    // Check if this is a special "clear all" action
    const clearAction = toasts.find(toast => toast.isCloseAction === true);
    
    if (clearAction) {
      // Clear all active toasts
      this.activeToasts.forEach(toast => {
        if (toast.timeoutRef) {
          clearTimeout(toast.timeoutRef);
          toast.timeoutRef = null;
        }
        toast.removing = true;
      });
      
      // Remove the action message itself from the array
      const filteredToasts = toasts.filter(toast => !toast.isCloseAction);
      this.activeToasts = [...filteredToasts];
      return;
    }
    
    // Filter out toasts marked for removal
    this.activeToasts = this.activeToasts.filter(toast => !toast.removing);
    
    // Process regular toast messages
    toasts.forEach(toast => {
      // Set up auto-dismiss for new toasts
      if (!toast.timeoutRef && !toast.removing) {
        this.setupAutoDismiss(toast);
      }
    });
    
    // Add new toasts
    this.activeToasts = [...this.activeToasts, ...toasts];
  }

  /**
   * Sets up auto-dismiss timer for a toast
   * @param toast The toast message to set up auto-dismiss for
   */
  setupAutoDismiss(toast: ToastMessage): void {
    // Set up timeout for auto-dismissal
    const timeoutRef = setTimeout(() => {
      toast.removing = true;
      setTimeout(() => {
        this.removeToast(toast);
      }, 300); // Wait for animation to complete
    }, toast.duration || 5000); // Default to 5 seconds if not specified
    
    // Store timeout reference for cleanup
    toast.timeoutRef = timeoutRef;
  }

  /**
   * Handles manual closing of a toast by user
   * @param toast The toast message to close
   */
  closeToast(toast: ToastMessage): void {
    // Mark toast for removal
    toast.removing = true;
    
    // Clear existing timeout
    if (toast.timeoutRef) {
      clearTimeout(toast.timeoutRef);
      toast.timeoutRef = null;
    }
    
    // Remove after animation completes
    setTimeout(() => {
      this.removeToast(toast);
    }, 300);
  }

  /**
   * Removes a toast from the service
   * @param toast The toast message to remove
   */
  removeToast(toast: ToastMessage): void {
    // Remove from service
    this.toastService.remove(toast.timestamp);
  }

  /**
   * Clears all toast timeouts
   */
  clearTimeouts(): void {
    // Clear all timeouts
    this.activeToasts.forEach(toast => {
      if (toast.timeoutRef) {
        clearTimeout(toast.timeoutRef);
        toast.timeoutRef = null;
      }
    });
  }

  /**
   * Tracking function for ngFor directive to optimize rendering
   * @param index Item index in the array
   * @param toast Toast message object
   * @returns Unique identifier for the toast
   */
  trackByFn(index: number, toast: ToastMessage): number {
    return toast.timestamp;
  }
}