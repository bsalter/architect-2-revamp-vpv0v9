import { Injectable } from '@angular/core'; // @angular/core 16.2.0
import { 
  HttpInterceptor, 
  HttpRequest, 
  HttpHandler, 
  HttpEvent, 
  HttpErrorResponse 
} from '@angular/common/http'; // @angular/common/http 16.2.0
import { Observable, throwError } from 'rxjs'; // rxjs 7.8.1
import { catchError, switchMap, retry } from 'rxjs/operators'; // rxjs/operators 7.8.1

import { ErrorHandlerService } from './error-handler.service';
import { AuthService } from '../auth/auth.service';
import { PerformanceMonitoringService } from '../monitoring/performance-monitoring.service';

/**
 * Intercepts HTTP requests to handle errors consistently across the application.
 * Implements error handling patterns including graceful degradation, user-friendly
 * error messages, retry logic for transient failures, and token refresh for
 * authentication errors.
 */
@Injectable()
export class HttpErrorInterceptor implements HttpInterceptor {
  /**
   * Maximum number of retry attempts for eligible requests
   */
  private maxRetries = 2;

  /**
   * Set of API endpoints eligible for retry on failure
   */
  private retryEndpoints = new Set<string>([
    '/api/interactions',
    '/api/search/interactions',
    '/api/sites'
  ]);

  /**
   * Set of HTTP status codes that are considered retryable
   */
  private retryableStatusCodes = new Set<number>([
    408, // Request Timeout
    429, // Too Many Requests
    502, // Bad Gateway
    503, // Service Unavailable
    504  // Gateway Timeout
  ]);

  /**
   * Initializes the HTTP error interceptor with required dependencies.
   * 
   * @param errorHandler Service for processing HTTP errors
   * @param authService Service for authentication token management
   * @param monitoringService Service for logging errors and performance metrics
   */
  constructor(
    private errorHandler: ErrorHandlerService,
    private authService: AuthService,
    private monitoringService: PerformanceMonitoringService
  ) {}

  /**
   * Intercepts HTTP requests and handles errors if they occur.
   * Implements:
   * 1. Retry logic with exponential backoff for transient errors
   * 2. Authentication token refresh for 401 errors
   * 3. Generic error handling for all other errors
   * 
   * @param request The outgoing HTTP request
   * @param next The next interceptor in the chain
   * @returns Observable of HTTP events with error handling
   */
  intercept(request: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    return next.handle(request).pipe(
      // Apply conditional retry logic
      retry({
        count: this.shouldRetry(request) ? this.maxRetries : 0,
        delay: (error, retryCount) => {
          if (error instanceof HttpErrorResponse) {
            // Only retry if the error is retryable
            if (this.retryableStatusCodes.has(error.status) && 
                this.shouldRetry(request, error)) {
              // Exponential backoff: 1s, 2s, 4s, etc.
              const delay = 1000 * Math.pow(2, retryCount - 1);
              return new Observable(subscriber => {
                setTimeout(() => subscriber.complete(), delay);
              });
            }
          }
          // Don't retry for other errors
          return throwError(() => error);
        }
      }),
      catchError((error: HttpErrorResponse) => {
        // Handle 401 Unauthorized errors by attempting to refresh the token
        if (error.status === 401) {
          return this.handleAuthError(request, next);
        }
        
        // For other errors, process through the error handler
        return this.handleGenericError(error, request);
      })
    );
  }

  /**
   * Determines if a failed request should be retried based on endpoint and status code.
   * 
   * @param request The HTTP request that failed
   * @param error Optional HTTP error response
   * @returns True if the request should be retried
   */
  private shouldRetry(request: HttpRequest<any>, error?: HttpErrorResponse): boolean {
    // Check if the URL matches any of the retry-eligible endpoints
    const url = request.url;
    let isRetryableEndpoint = false;
    
    for (const endpoint of this.retryEndpoints) {
      if (url.includes(endpoint)) {
        isRetryableEndpoint = true;
        break;
      }
    }
    
    // If no error provided, just check the endpoint
    if (!error) {
      return isRetryableEndpoint;
    }
    
    // Check if the status code is retryable
    const isRetryableStatus = this.retryableStatusCodes.has(error.status);
    
    // Only retry if both conditions are met
    return isRetryableEndpoint && isRetryableStatus;
  }

  /**
   * Handles 401 Unauthorized errors by refreshing the authentication token.
   * 
   * @param request The original HTTP request that failed
   * @param next The next HTTP handler in the chain
   * @returns Observable of HTTP events after token refresh
   */
  private handleAuthError(request: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    return this.authService.refreshToken().pipe(
      switchMap(token => {
        if (token) {
          // Clone the request with the new token
          return next.handle(this.addAuthorizationHeader(request, token));
        } else {
          // Token refresh failed, proceed with error
          return throwError(() => new HttpErrorResponse({
            error: 'Authentication required',
            status: 401,
            statusText: 'Unauthorized'
          }));
        }
      }),
      catchError(refreshError => {
        // Token refresh failed, process the error
        this.monitoringService.logError(refreshError, 'Token refresh failed');
        return throwError(() => refreshError);
      })
    );
  }

  /**
   * Clones a request and adds the Bearer token to the Authorization header.
   * 
   * @param request The HTTP request to clone
   * @param token The authentication token to add
   * @returns Cloned request with Authorization header
   */
  private addAuthorizationHeader(request: HttpRequest<any>, token: string): HttpRequest<any> {
    return request.clone({
      setHeaders: {
        Authorization: `Bearer ${token}`
      }
    });
  }

  /**
   * Processes non-authentication errors through the error handler service.
   * 
   * @param error The HTTP error response
   * @param request The original HTTP request
   * @returns Observable that immediately emits an error
   */
  private handleGenericError(error: HttpErrorResponse, request: HttpRequest<any>): Observable<never> {
    // Extract context information for error tracking
    const context = {
      url: request.url,
      method: request.method,
      headers: request.headers.keys().reduce((obj, key) => {
        // Exclude Authorization header for security
        if (key !== 'Authorization') {
          obj[key] = request.headers.get(key);
        }
        return obj;
      }, {} as Record<string, string | null>),
      params: request.params.keys().reduce((obj, key) => {
        obj[key] = request.params.get(key);
        return obj;
      }, {} as Record<string, string | null>)
    };
    
    // Process the error through the error handler service
    this.errorHandler.handleHttpError(error, context);
    
    // Log the error to the monitoring service
    this.monitoringService.logError(error, `HTTP Error: ${request.method} ${request.url}`);
    
    // Return an observable that immediately emits the error
    return throwError(() => error);
  }
}