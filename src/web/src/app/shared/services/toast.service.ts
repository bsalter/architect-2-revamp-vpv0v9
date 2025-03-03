import { Injectable } from '@angular/core'; // @angular/core 16.2.0
import { BehaviorSubject, Observable } from 'rxjs'; // rxjs 7.8.1

/**
 * Interface defining the structure of toast notifications.
 */
export interface ToastMessage {
  /** Type of toast notification (success, error, warning, info) */
  type: string;
  /** Content message of the toast */
  message: string;
  /** Title of the toast */
  title: string;
  /** Duration in milliseconds before auto-dismissal */
  duration: number;
  /** Unique timestamp identifier for the toast */
  timestamp: number;
  /** Flag indicating if this is a special clear action */
  isCloseAction?: boolean;
  /** Flag indicating if toast is in process of being removed */
  removing?: boolean;
  /** Reference to timeout for auto-dismissal */
  timeoutRef?: any;
}

/**
 * Interface defining optional configuration for toast notifications.
 */
export interface ToastOptions {
  /** Optional custom title for the toast */
  title?: string;
  /** Optional custom duration in milliseconds */
  duration?: number;
}

/**
 * Service that manages toast notifications across the application.
 * Provides a centralized mechanism for displaying and managing toast messages
 * with support for different types (success, error, warning, info).
 */
@Injectable({
  providedIn: 'root'
})
export class ToastService {
  /** BehaviorSubject to track and emit toast message changes */
  private toastSubject: BehaviorSubject<ToastMessage[]> = new BehaviorSubject<ToastMessage[]>([]);
  /** Observable of toast messages that components can subscribe to */
  private toasts$: Observable<ToastMessage[]> = this.toastSubject.asObservable();
  /** Default duration for toasts in milliseconds */
  private defaultDuration = 5000;

  /**
   * Initializes the toast service.
   */
  constructor() {
    // Initialization is handled through property initialization
  }

  /**
   * Gets the observable stream of active toast messages.
   * Components can subscribe to this to display toast notifications.
   * 
   * @returns Observable stream of toast messages
   */
  getToasts(): Observable<ToastMessage[]> {
    return this.toasts$;
  }

  /**
   * Shows a toast notification with given type, message, and options.
   * 
   * @param type The type of toast (success, error, warning, info)
   * @param message The message content to display
   * @param options Optional configuration options
   */
  show(type: string, message: string, options: ToastOptions = {}): void {
    const toast: ToastMessage = {
      type,
      message,
      timestamp: Date.now(),
      title: options.title || this.getDefaultTitle(type),
      duration: options.duration || this.defaultDuration
    };

    const currentToasts = this.toastSubject.getValue();
    this.toastSubject.next([...currentToasts, toast]);
  }

  /**
   * Shows a success toast notification.
   * 
   * @param message The success message content to display
   * @param options Optional configuration options
   */
  showSuccess(message: string, options: ToastOptions = {}): void {
    this.show('success', message, options);
  }

  /**
   * Shows an error toast notification.
   * 
   * @param message The error message content to display
   * @param options Optional configuration options
   */
  showError(message: string, options: ToastOptions = {}): void {
    this.show('error', message, options);
  }

  /**
   * Shows a warning toast notification.
   * 
   * @param message The warning message content to display
   * @param options Optional configuration options
   */
  showWarning(message: string, options: ToastOptions = {}): void {
    this.show('warning', message, options);
  }

  /**
   * Shows an informational toast notification.
   * 
   * @param message The informational message content to display
   * @param options Optional configuration options
   */
  showInfo(message: string, options: ToastOptions = {}): void {
    this.show('info', message, options);
  }

  /**
   * Clears all active toast notifications.
   * Sends a special clear action that can be handled by the toast component.
   */
  clear(): void {
    // Create a special toast with isCloseAction flag to signal clearing all toasts
    const clearAction: ToastMessage = {
      type: 'clear',
      message: '',
      title: '',
      duration: 0,
      timestamp: Date.now(),
      isCloseAction: true
    };
    
    this.toastSubject.next([clearAction]);
  }

  /**
   * Removes a specific toast by its timestamp.
   * 
   * @param timestamp The unique timestamp identifier of the toast to remove
   */
  remove(timestamp: number): void {
    const currentToasts = this.toastSubject.getValue();
    const filteredToasts = currentToasts.filter(toast => toast.timestamp !== timestamp);
    this.toastSubject.next(filteredToasts);
  }

  /**
   * Gets the default title based on toast type.
   * 
   * @param type The type of toast
   * @returns Default title for the toast type
   */
  private getDefaultTitle(type: string): string {
    switch (type) {
      case 'success':
        return 'Success';
      case 'error':
        return 'Error';
      case 'warning':
        return 'Warning';
      case 'info':
        return 'Information';
      default:
        return 'Notification';
    }
  }
}