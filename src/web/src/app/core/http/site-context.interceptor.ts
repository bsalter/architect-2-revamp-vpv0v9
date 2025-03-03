import { Injectable } from '@angular/core'; // v16.2.0
import { HttpInterceptor, HttpRequest, HttpHandler, HttpEvent } from '@angular/common/http'; // v16.2.0
import { Observable } from 'rxjs'; // v7.8.1
import { take } from 'rxjs/operators'; // v7.8.1

import { UserContextService } from '../auth/user-context.service';
import { SiteSelectionService } from '../auth/site-selection.service';

/**
 * HTTP interceptor that adds the current site context to all outgoing API requests
 * to ensure site-scoped data access. This is a critical component of the application's
 * multi-tenant security architecture, enforcing data boundaries between organizational sites.
 */
@Injectable()
export class SiteContextInterceptor implements HttpInterceptor {
  /**
   * Paths that should be excluded from site context enforcement
   * These paths include authentication endpoints and site-related endpoints
   * that don't require (or occur before) site context
   */
  private excludedPaths: string[] = [
    'auth/login',
    'auth/refresh',
    'auth/logout',
    'sites',
    'users/sites'
  ];

  /**
   * Creates an instance of SiteContextInterceptor.
   * 
   * @param userContextService Service for accessing user context including current site
   * @param siteSelectionService Service for checking site selection status
   */
  constructor(
    private userContextService: UserContextService,
    private siteSelectionService: SiteSelectionService
  ) {}

  /**
   * Intercepts HTTP requests and adds site context information.
   * This is a crucial part of the site-scoped access control mechanism,
   * ensuring that all data requests are properly filtered by the user's current site.
   * 
   * @param request The outgoing HTTP request
   * @param next The next handler in the chain
   * @returns Observable of HTTP events
   */
  intercept(request: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    // Skip site context for excluded paths (auth endpoints, etc.)
    if (this.shouldExcludePath(request.url)) {
      return next.handle(request);
    }

    // Get current site ID
    const currentSiteId = this.userContextService.getCurrentSiteId();

    if (currentSiteId) {
      // If site ID is available, add it to the request
      request = this.addSiteContext(request, currentSiteId);
    } else {
      // If site ID is not available but path requires it, log a warning
      console.warn(`No site context available for request to ${request.url}`);
    }

    // Forward the modified request
    return next.handle(request);
  }

  /**
   * Determines if a request URL should be excluded from site context enhancement.
   * Certain paths like authentication endpoints don't need or can't have site context.
   * 
   * @param url The URL to check
   * @returns True if the path should be excluded from site context
   */
  private shouldExcludePath(url: string): boolean {
    return this.excludedPaths.some(path => url.includes(path));
  }

  /**
   * Adds site context to a request based on the HTTP method.
   * - For GET/DELETE: Adds site_id as a query parameter
   * - For POST/PUT with body: Adds site_id to the request body
   * - For POST/PUT without body: Adds site_id as a query parameter
   * 
   * @param request The original HTTP request
   * @param siteId The site ID to add to the request
   * @returns A new request with site context added
   */
  private addSiteContext(request: HttpRequest<any>, siteId: number): HttpRequest<any> {
    // For GET/DELETE requests, add site_id as a query parameter
    if (request.method === 'GET' || request.method === 'DELETE') {
      // Don't override if site_id is already present in the request
      if (!request.params.has('site_id')) {
        const params = request.params.set('site_id', siteId.toString());
        return request.clone({ params });
      }
      return request;
    } 
    
    // For POST/PUT requests, behavior depends on whether there's a body
    if (request.method === 'POST' || request.method === 'PUT') {
      // If there's a body and it's an object (not FormData, etc.), add site_id to it
      if (request.body && typeof request.body === 'object' && !request.body.site_id) {
        const body = { ...request.body, site_id: siteId };
        return request.clone({ body });
      } 
      // If there's no body, add site_id as a query parameter
      else if (!request.body) {
        const params = request.params.set('site_id', siteId.toString());
        return request.clone({ params });
      }
      // If body exists but isn't an object we can add to, return unchanged
      return request;
    }
    
    // For other HTTP methods (PATCH, etc.), return the original request
    return request;
  }
}