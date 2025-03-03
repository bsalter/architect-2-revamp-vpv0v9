import { Injectable } from '@angular/core'; // v16.2.0
import { 
  HttpInterceptor,
  HttpRequest,
  HttpHandler,
  HttpEvent,
  HttpErrorResponse,
  HTTP_INTERCEPTORS 
} from '@angular/common/http'; // v16.2.0
import { Observable, throwError } from 'rxjs'; // v7.8.1
import { catchError, switchMap } from 'rxjs/operators'; // v7.8.1

import { TokenService } from './token.service';
import { AuthService } from './auth.service';
import { UserContextService } from './user-context.service';
import { environment } from '../../../environments/environment';

/**
 * HTTP interceptor that automatically adds the JWT token to outgoing requests
 * and handles token refresh when expired tokens are detected.
 */
@Injectable()
export class JwtInterceptor implements HttpInterceptor {
  private isRefreshing = false;

  constructor(
    private tokenService: TokenService,
    private authService: AuthService,
    private userContextService: UserContextService
  ) {}

  /**
   * Intercepts HTTP requests to add authorization and site context headers
   * 
   * @param request The HTTP request to modify
   * @param next The HTTP handler
   * @returns Observable of HTTP events
   */
  intercept(request: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    // Only add auth headers to API requests
    if (!this.isApiRequest(request)) {
      return next.handle(request);
    }

    // Get the JWT token from the token service
    const token = this.tokenService.getToken();
    
    // Clone request and add authorization and site context headers
    let modifiedRequest = request;
    
    if (token) {
      // Add authorization header
      modifiedRequest = this.addAuthorizationHeader(request, token);
      
      // Add site context header
      modifiedRequest = this.addSiteContextHeader(modifiedRequest);
    }

    // Process the modified request
    return next.handle(modifiedRequest).pipe(
      catchError(error => {
        // Handle token expiration
        if (
          error instanceof HttpErrorResponse &&
          (error.status === 401 || error.status === 403) &&
          this.tokenService.isTokenExpired()
        ) {
          return this.handleExpiredToken(request, next);
        }
        
        // Pass through all other errors
        return throwError(() => error);
      })
    );
  }

  /**
   * Adds JWT token to the Authorization header of a request
   * 
   * @param request The HTTP request to modify
   * @param token The JWT token to add
   * @returns Modified request with Authorization header
   */
  private addAuthorizationHeader(request: HttpRequest<any>, token: string): HttpRequest<any> {
    return request.clone({
      setHeaders: {
        Authorization: `Bearer ${token}`
      }
    });
  }

  /**
   * Adds site context header to identify the current active site
   * 
   * @param request The HTTP request to modify
   * @returns Modified request with site context header
   */
  private addSiteContextHeader(request: HttpRequest<any>): HttpRequest<any> {
    const siteId = this.userContextService.getCurrentSiteId();
    
    if (siteId) {
      return request.clone({
        setHeaders: {
          'X-Site-Context': siteId.toString()
        }
      });
    }
    
    return request;
  }

  /**
   * Handles expired token by attempting to refresh and retrying the original request
   * 
   * @param request The original HTTP request
   * @param next The HTTP handler
   * @returns Observable with refreshed token and retried request
   */
  private handleExpiredToken(request: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    // Prevent infinite refresh loops
    if (this.isRefreshing) {
      return throwError(() => new Error('Token refresh already in progress'));
    }
    
    this.isRefreshing = true;
    
    // Attempt to refresh the token
    return this.authService.refreshSession().pipe(
      switchMap(newToken => {
        this.isRefreshing = false;
        
        if (!newToken) {
          return throwError(() => new Error('Failed to refresh token'));
        }
        
        // Update request with new token
        let updatedRequest = this.addAuthorizationHeader(request, newToken);
        updatedRequest = this.addSiteContextHeader(updatedRequest);
        
        // Retry the request with the new token
        return next.handle(updatedRequest);
      }),
      catchError(error => {
        this.isRefreshing = false;
        return throwError(() => error);
      })
    );
  }

  /**
   * Determines if a request is targeting the API based on URL
   * 
   * @param request The HTTP request to check
   * @returns True if request targets the API
   */
  private isApiRequest(request: HttpRequest<any>): boolean {
    if (!environment.production) {
      // Log the request URL in development for debugging
      console.debug(`Request URL: ${request.url}, API URL: ${environment.apiUrl}`);
    }
    return request.url.startsWith(environment.apiUrl);
  }
}

/**
 * Provider for the JWT interceptor to be included in app module providers
 */
export const JWT_INTERCEPTOR_PROVIDER = {
  provide: HTTP_INTERCEPTORS,
  useClass: JwtInterceptor,
  multi: true
};