import { Injectable, ErrorHandler } from '@angular/core'; // @angular/core 16.2.0
import { HttpErrorResponse } from '@angular/common/http'; // @angular/common/http 16.2.0
import { ErrorHandlerService } from './error-handler.service';
import { PerformanceMonitoringService } from '../monitoring/performance-monitoring.service';
import { environment } from '../../../environments/environment';
import { UserActivityService } from '../monitoring/user-activity.service';

/**
 * Custom implementation of Angular's ErrorHandler that provides centralized error handling
 * across the application. It intercepts and processes all unhandled exceptions, ensuring 
 * they are properly logged, reported to monitoring services, and presented to users with 
 * appropriate feedback when necessary.
 */
@Injectable()
export class GlobalErrorHandler extends ErrorHandler {
  /** Whether application is running in production mode */
  private isProduction: boolean;
  
  /** Whether to output errors to browser console */
  private enableConsoleLogging: boolean;
  
  /** Whether to track errors in performance monitoring */
  private enableErrorTracking: boolean;

  /**
   * Initializes the global error handler with required dependencies
   * 
   * @param errorHandlerService Service for standardized error processing
   * @param monitoringService Service for tracking performance and errors
   * @param userActivityService Service for tracking user activity events
   */
  constructor(
    private errorHandlerService: ErrorHandlerService,
    private monitoringService: PerformanceMonitoringService,
    private userActivityService: UserActivityService
  ) {
    super(); // Call parent ErrorHandler constructor
    
    // Initialize configuration from environment
    this.isProduction = environment.production;
    this.enableConsoleLogging = environment.logging?.enableConsoleLogging ?? true;
    this.enableErrorTracking = environment.logging?.errorTracking ?? true;
  }

  /**
   * Overrides Angular's handleError method to process all unhandled exceptions
   * 
   * @param error Any unhandled exception thrown within the application
   */
  override handleError(error: any): void {
    try {
      const errorSource = this.getErrorSource(error);
      
      // For HTTP errors, we should avoid duplicating HTTP interceptor handling
      // which is managed by the HttpInterceptor chain
      if (error instanceof HttpErrorResponse) {
        // HTTP errors are typically handled by interceptors
        // We might still want to log certain critical HTTP errors
        if (error.status >= 500 && this.enableConsoleLogging) {
          console.error(`Server error (${error.status}) caught by GlobalErrorHandler:`, error.message);
        }
        return;
      }
      
      // Log to console in development or if console logging is enabled
      if (this.enableConsoleLogging) {
        if (this.isProduction) {
          // In production, log with minimal details to avoid sensitive information
          console.error(`Error occurred in ${errorSource}: ${error.message || 'Unknown error'}`);
        } else {
          // In development, include full error details for debugging
          console.error(`Error in ${errorSource}:`, error);
          console.error('Error stack:', error.stack);
        }
      }
      
      // Track error in monitoring service if enabled
      if (this.enableErrorTracking) {
        this.monitoringService.trackError(error, errorSource);
      }
      
      // Track as user activity event for analytics
      if (this.shouldReportError(error)) {
        this.userActivityService.trackActivity('error', {
          message: error.message,
          source: errorSource,
          stack: !this.isProduction ? error.stack : undefined,
          timestamp: new Date().toISOString()
        });
      }
      
      // Delegate to the error handler service for standardized processing
      // This will handle user notifications, potential recovery actions, etc.
      this.errorHandlerService.handleError(error, errorSource);
      
    } catch (handlingError) {
      // Last resort error handling if our error handler itself fails
      // This is critical to ensure the error handler doesn't break the application
      console.error('Error occurred within error handler:', handlingError);
      console.error('Original error:', error);
    }
  }
  
  /**
   * Determines the source context of an error to provide better error tracking
   * 
   * @param error The error to analyze
   * @returns Source context identifier
   */
  private getErrorSource(error: Error): string {
    try {
      if (!error) return 'unknown';
      
      // Try to extract component or service name from stack trace
      const stack = error.stack || '';
      
      // Look for component or directive names in stack
      const componentMatch = stack.match(/at\s+(\w+Component)\./);
      if (componentMatch && componentMatch[1]) {
        return `Component:${componentMatch[1]}`;
      }
      
      // Look for service names in stack
      const serviceMatch = stack.match(/at\s+(\w+Service)\./);
      if (serviceMatch && serviceMatch[1]) {
        return `Service:${serviceMatch[1]}`;
      }
      
      // Look for pipe names in stack
      const pipeMatch = stack.match(/at\s+(\w+Pipe)\./);
      if (pipeMatch && pipeMatch[1]) {
        return `Pipe:${pipeMatch[1]}`;
      }
      
      // Look for references to template errors
      if (stack.includes('TemplateError') || stack.includes('template.html')) {
        return 'Template';
      }
      
      // Check for module or initialization errors
      if (stack.includes('Module.') || stack.includes('bootstrapModule')) {
        return 'NgModule';
      }
      
      // Check for router errors
      if (stack.includes('Router') || stack.includes('NavigationError')) {
        return 'Router';
      }
      
      return 'unknown';
    } catch (e) {
      // If error source detection fails, return a generic source
      return 'unknown';
    }
  }
  
  /**
   * Determines if an error should be reported to monitoring services
   * Filters out expected errors that don't represent actual issues
   * 
   * @param error The error to evaluate
   * @returns True if error should be reported, false otherwise
   */
  private shouldReportError(error: Error): boolean {
    if (!error) return false;
    
    const errorMessage = error.message || '';
    const errorStack = error.stack || '';
    
    // Skip canceled HTTP requests (not actual errors)
    if (
      errorMessage.includes('cancelled') || 
      errorMessage.includes('canceled') || 
      errorMessage.includes('aborted')
    ) {
      return false;
    }
    
    // Skip navigation cancellations (usually due to route guards)
    if (
      errorMessage.includes('Navigation cancelled') || 
      errorMessage.includes('NavigationCancel')
    ) {
      return false;
    }
    
    // Skip some common third-party library errors that may not be critical
    if (
      errorMessage.includes('ResizeObserver loop') || // Chrome ResizeObserver error
      errorMessage.includes('Script error') || // Cross-origin script errors with limited info
      errorStack.includes('zone-evergreen.js') || // Some Zone.js internal errors
      errorStack.includes('polyfills.js')
    ) {
      return false;
    }
    
    // Default to reporting all other errors
    return true;
  }
}