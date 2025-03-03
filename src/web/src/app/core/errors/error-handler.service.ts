import { Injectable } from '@angular/core'; // @angular/core 16.2.0
import { HttpErrorResponse } from '@angular/common/http'; // @angular/common/http 16.2.0
import { Router } from '@angular/router'; // @angular/router 16.2.0
import { ToastService } from '../../shared/services/toast.service';
import { PerformanceMonitoringService } from '../monitoring/performance-monitoring.service';
import { environment } from '../../../environments/environment';

/**
 * Service that provides centralized error handling for the application.
 * Implements standardized processing for different error types with appropriate
 * user feedback and logging capabilities.
 */
@Injectable({
  providedIn: 'root'
})
export class ErrorHandlerService {
  /** Whether to output errors to the browser console */
  private enableConsoleLogging: boolean;
  
  /** Whether to send errors to remote logging service */
  private enableRemoteLogging: boolean;
  
  /** Whether to track errors in performance monitoring */
  private enableErrorTracking: boolean;
  
  /** Whether application is running in production mode */
  private isProduction: boolean;

  /**
   * Initializes the error handler service with required dependencies.
   * 
   * @param toastService Service for displaying toast notifications
   * @param monitoringService Service for logging and monitoring errors
   * @param router Router for navigation after critical errors
   */
  constructor(
    private toastService: ToastService,
    private monitoringService: PerformanceMonitoringService,
    private router: Router
  ) {
    // Initialize logging configuration from environment
    this.enableConsoleLogging = environment.logging?.enableConsoleLogging ?? true;
    this.enableRemoteLogging = environment.logging?.enableRemoteLogging ?? false;
    this.enableErrorTracking = environment.logging?.errorTracking ?? true;
    this.isProduction = environment.production;
  }

  /**
   * Handles any type of error with appropriate actions and user feedback.
   * 
   * @param error The error object to handle
   * @param source Optional source identifier where the error occurred
   * @param showToast Whether to show a toast notification to the user (default: true)
   */
  handleError(error: Error | any, source?: string, showToast: boolean = true): void {
    // Log error details to console if enabled
    if (this.enableConsoleLogging) {
      console.error(`Error in ${source || 'unknown source'}:`, error);
    }

    // Track error in monitoring service if enabled
    if (this.enableErrorTracking) {
      this.monitoringService.logError(error, source || 'application');
    }

    // Extract user-friendly error message
    const errorMessage = this.extractErrorMessage(error);

    // Show toast notification if enabled
    if (showToast) {
      this.toastService.showError(errorMessage);
    }

    // Check if this is a critical error requiring application recovery
    if (error instanceof Error && this.isCriticalError(error)) {
      this.handleCriticalError(error);
    }
  }

  /**
   * Handles HTTP error responses from API calls.
   * 
   * @param error The HTTP error response
   * @param context Additional context for the error
   * @param showToast Whether to show a toast notification (default: true)
   * @returns A standardized error response object
   */
  handleHttpError(error: HttpErrorResponse, context?: any, showToast: boolean = true): any {
    let errorMessage = '';
    let errorType = 'server-error';
    let statusCode = 500;

    if (error instanceof HttpErrorResponse) {
      statusCode = error.status;

      // Categorize error based on status code
      if (error.status === 0) {
        errorType = 'network-error';
        errorMessage = 'Unable to connect to the server. Please check your network connection.';
      } else if (error.status >= 400 && error.status < 500) {
        errorType = 'client-error';
        
        // Special handling for common client error status codes
        if (error.status === 401) {
          errorMessage = 'Authentication required. Please log in again.';
          // Redirect to login page
          setTimeout(() => {
            this.router.navigate(['/login']);
          }, 1500);
        } else if (error.status === 403) {
          errorMessage = 'You do not have permission to perform this action.';
        } else if (error.status === 404) {
          errorMessage = 'The requested resource was not found.';
        } else if (error.status === 422) {
          errorMessage = 'Validation error. Please check your input.';
        } else {
          errorMessage = error.error?.message || error.message || 'An error occurred while processing your request.';
        }
      } else {
        errorType = 'server-error';
        errorMessage = this.isProduction 
          ? 'A server error occurred. Please try again later.'
          : (error.error?.message || error.message || 'Server error');
      }
    } else {
      errorMessage = this.extractErrorMessage(error);
    }

    // Log error details
    if (this.enableConsoleLogging) {
      console.error('HTTP Error:', {
        status: statusCode,
        type: errorType,
        message: errorMessage,
        error,
        context
      });
    }

    // Track error in monitoring
    if (this.enableErrorTracking) {
      this.monitoringService.logError(error, `HTTP Error ${statusCode}`);
    }

    // Show toast notification if enabled
    if (showToast) {
      this.toastService.showError(errorMessage);
    }

    // Return a standardized error response object
    return {
      success: false,
      statusCode,
      errorType,
      message: errorMessage,
      timestamp: new Date(),
      originalError: this.isProduction ? undefined : error
    };
  }

  /**
   * Handles form validation errors.
   * 
   * @param validationErrors Object containing validation errors
   * @param showToast Whether to show a toast notification (default: true)
   */
  handleValidationError(validationErrors: any, showToast: boolean = true): void {
    // Format validation errors into a user-friendly message
    let errorMessage = 'Please correct the following errors:';
    const errorDetails: string[] = [];

    if (validationErrors) {
      if (typeof validationErrors === 'string') {
        errorDetails.push(validationErrors);
      } else if (validationErrors instanceof Array) {
        errorDetails.push(...validationErrors);
      } else if (typeof validationErrors === 'object') {
        // Extract error messages from validation error object
        Object.keys(validationErrors).forEach(key => {
          const value = validationErrors[key];
          if (typeof value === 'string') {
            errorDetails.push(value);
          } else if (value instanceof Array) {
            errorDetails.push(...value);
          }
        });
      }
    }

    if (errorDetails.length > 0) {
      // Format error message with details if available
      errorMessage = errorDetails.length === 1 
        ? errorDetails[0] 
        : `Please correct the following errors: ${errorDetails.join(', ')}`;
    }

    // Log validation errors
    if (this.enableConsoleLogging) {
      console.warn('Validation errors:', validationErrors);
    }

    // Show toast notification if enabled
    if (showToast) {
      this.toastService.showWarning(errorMessage, { title: 'Validation Error' });
    }
  }

  /**
   * Extracts a user-friendly error message from various error types.
   * 
   * @param error The error object
   * @returns A user-friendly error message string
   */
  private extractErrorMessage(error: any): string {
    if (!error) {
      return 'An unexpected error occurred.';
    }

    // Handle different error types
    if (error instanceof HttpErrorResponse) {
      if (error.status === 0) {
        return 'Unable to connect to the server. Please check your network connection.';
      }
      
      // Try to extract error message from response
      const serverError = error.error;
      
      if (serverError) {
        if (typeof serverError === 'string') {
          return serverError;
        }
        if (serverError.message) {
          return serverError.message;
        }
        if (serverError.error) {
          return serverError.error;
        }
      }
      
      return error.message || `${error.status} ${error.statusText}`;
    }

    if (error instanceof Error) {
      return error.message;
    }

    if (typeof error === 'string') {
      return error;
    }

    if (typeof error === 'object') {
      return error.message || error.error || JSON.stringify(error);
    }

    return 'An unexpected error occurred.';
  }

  /**
   * Determines if an error is critical and requires application recovery.
   * 
   * @param error The error to evaluate
   * @returns True if the error is critical, false otherwise
   */
  private isCriticalError(error: Error): boolean {
    // Check for specific error types that are considered critical
    const errorMessage = error.message || '';
    const errorStack = error.stack || '';
    
    // Memory-related errors are typically critical
    if (errorMessage.includes('out of memory') || 
        errorMessage.includes('heap limit exceeded')) {
      return true;
    }
    
    // Check for unrecoverable state corruption
    if (errorMessage.includes('unrecoverable state') || 
        errorMessage.includes('corrupted')) {
      return true;
    }
    
    // Check for errors that indicate the application can't continue normally
    if (errorMessage.includes('fatal') ||
        errorMessage.includes('catastrophic')) {
      return true;
    }

    // Additional checks based on error types or properties could be added here
    
    return false;
  }

  /**
   * Handles critical errors that require application recovery.
   * 
   * @param error The critical error to handle
   */
  private handleCriticalError(error: Error): void {
    // Log critical error with high visibility
    console.error('CRITICAL ERROR - Application Recovery Required:', error);
    
    // Attempt to save any user data if possible
    // (Implementation would depend on application needs)
    
    // Notify user of the critical error
    this.toastService.showError(
      'A critical error has occurred. The application will reload to recover.',
      { title: 'Critical Error', duration: 10000 }
    );
    
    // Redirect to error page or reload application
    setTimeout(() => {
      try {
        // First attempt to navigate to an error page
        this.router.navigate(['/error'], { 
          state: { errorMessage: this.extractErrorMessage(error) }
        });
      } catch (e) {
        // If navigation fails, reload the application
        window.location.reload();
      }
    }, 3000);
  }
}