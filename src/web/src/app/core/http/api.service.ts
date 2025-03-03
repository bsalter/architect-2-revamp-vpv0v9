import { Injectable } from '@angular/core'; // v16.2.0
import { HttpClient, HttpHeaders, HttpParams, HttpErrorResponse } from '@angular/common/http'; // v16.2.0
import { Observable, throwError, of } from 'rxjs'; // v7.8.1
import { catchError, tap, map, finalize } from 'rxjs/operators'; // v7.8.1

import { environment } from '../../../environments/environment';
import { TokenService } from '../auth/token.service';
import { SiteSelectionService } from '../auth/site-selection.service';
import { CacheService } from '../cache/cache.service';
import { ErrorHandlerService } from '../errors/error-handler.service';

/**
 * Core service that provides a centralized interface for making HTTP requests to the backend API.
 * Handles common HTTP operations (GET, POST, PUT, DELETE), implements request/response transformation,
 * error handling, caching, and ensures all requests are properly authenticated and site-scoped.
 */
@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private apiUrl: string;
  private cachingEnabled: boolean;
  private defaultCacheTtl: number;

  /**
   * Initializes the API service with required dependencies
   * 
   * @param http Angular's HttpClient for making API requests
   * @param tokenService Service to get authentication tokens
   * @param siteService Service to get current site context
   * @param cacheService Service for caching API responses
   * @param errorHandler Service for handling HTTP errors
   */
  constructor(
    private http: HttpClient,
    private tokenService: TokenService,
    private siteService: SiteSelectionService,
    private cacheService: CacheService,
    private errorHandler: ErrorHandlerService
  ) {
    this.apiUrl = environment.apiUrl;
    this.cachingEnabled = environment.caching?.enabled || false;
    this.defaultCacheTtl = environment.caching?.defaultTtl || 300; // 5 minutes default
  }

  /**
   * Performs an HTTP GET request to the specified endpoint with optional caching
   * 
   * @param endpoint The API endpoint to request
   * @param params Optional query parameters
   * @param useCache Whether to use caching for this request
   * @param cacheTtl Optional TTL for cache entry in milliseconds
   * @returns Observable with response data
   */
  get<T>(endpoint: string, params?: any, useCache: boolean = true, cacheTtl?: number): Observable<T> {
    const url = this.buildUrl(endpoint);
    let cacheKey: string | null = null;
    
    // Check cache for existing data if caching is enabled
    if (this.cachingEnabled && useCache) {
      cacheKey = this.generateCacheKey(url, params);
      const cachedData = this.cacheService.get(cacheKey);
      
      if (cachedData) {
        return of(cachedData as T);
      }
    }
    
    const httpParams = this.createHttpParams(params);
    const headers = this.createHttpHeaders();
    
    return this.http.get<T>(url, { params: httpParams, headers }).pipe(
      tap(response => {
        // Cache the response if caching is enabled
        if (this.cachingEnabled && useCache && cacheKey) {
          this.cacheService.set(cacheKey, response, cacheTtl || this.defaultCacheTtl);
        }
      }),
      catchError(error => {
        return throwError(() => this.errorHandler.handleHttpError(error, { endpoint, params }));
      })
    );
  }

  /**
   * Performs an HTTP POST request to the specified endpoint
   * 
   * @param endpoint The API endpoint to request
   * @param body The request body
   * @param options Optional request options
   * @returns Observable with response data
   */
  post<T>(endpoint: string, body: any, options?: any): Observable<T> {
    const url = this.buildUrl(endpoint);
    const headers = this.createHttpHeaders(options?.headers);
    
    return this.http.post<T>(url, body, { headers }).pipe(
      catchError(error => {
        return throwError(() => this.errorHandler.handleHttpError(error, { endpoint, body }));
      })
    );
  }

  /**
   * Performs an HTTP PUT request to the specified endpoint
   * 
   * @param endpoint The API endpoint to request
   * @param body The request body
   * @param options Optional request options
   * @returns Observable with response data
   */
  put<T>(endpoint: string, body: any, options?: any): Observable<T> {
    const url = this.buildUrl(endpoint);
    const headers = this.createHttpHeaders(options?.headers);
    
    return this.http.put<T>(url, body, { headers }).pipe(
      catchError(error => {
        return throwError(() => this.errorHandler.handleHttpError(error, { endpoint, body }));
      })
    );
  }

  /**
   * Performs an HTTP DELETE request to the specified endpoint
   * 
   * @param endpoint The API endpoint to request
   * @param options Optional request options
   * @returns Observable with response data
   */
  delete<T>(endpoint: string, options?: any): Observable<T> {
    const url = this.buildUrl(endpoint);
    const headers = this.createHttpHeaders(options?.headers);
    
    return this.http.delete<T>(url, { headers }).pipe(
      catchError(error => {
        return throwError(() => this.errorHandler.handleHttpError(error, { endpoint }));
      })
    );
  }

  /**
   * Creates HTTP headers with authentication token
   * 
   * @param additionalHeaders Optional additional headers
   * @returns HTTP headers with authorization and content type
   */
  private createHttpHeaders(additionalHeaders?: any): HttpHeaders {
    let headers = new HttpHeaders({
      'Content-Type': 'application/json'
    });
    
    const token = this.tokenService.getToken();
    if (token) {
      headers = headers.set('Authorization', `Bearer ${token}`);
    }
    
    if (additionalHeaders) {
      Object.keys(additionalHeaders).forEach(key => {
        headers = headers.set(key, additionalHeaders[key]);
      });
    }
    
    return headers;
  }

  /**
   * Converts an object to HttpParams for URL query parameters
   * 
   * @param params Object containing parameter key-value pairs
   * @returns HTTP params object for request
   */
  private createHttpParams(params?: any): HttpParams {
    let httpParams = new HttpParams();
    
    // Add site_id parameter for site-scoping if not already included
    const siteId = this.siteService.getCurrentSiteId();
    if (siteId && (!params || !params.site_id)) {
      httpParams = httpParams.set('site_id', siteId.toString());
    }
    
    // Convert object parameters to HttpParams
    if (params) {
      Object.keys(params).forEach(key => {
        const value = params[key];
        if (value !== undefined && value !== null) {
          if (Array.isArray(value)) {
            // Handle array parameters
            value.forEach(item => {
              httpParams = httpParams.append(key, item.toString());
            });
          } else {
            httpParams = httpParams.set(key, value.toString());
          }
        }
      });
    }
    
    return httpParams;
  }

  /**
   * Generates a unique cache key for a request
   * 
   * @param url The request URL
   * @param params Optional request parameters
   * @returns Cache key string
   */
  private generateCacheKey(url: string, params?: any): string {
    if (!params) return url;
    
    // Sort keys for consistent cache key generation regardless of parameter order
    const sortedKeys = Object.keys(params).sort();
    let cacheKey = url;
    
    sortedKeys.forEach(key => {
      const value = params[key];
      if (value !== undefined && value !== null) {
        if (Array.isArray(value)) {
          // Sort array values for consistent cache keys
          const sortedValues = [...value].sort();
          sortedValues.forEach(item => {
            cacheKey += `|${key}=${item}`;
          });
        } else {
          cacheKey += `|${key}=${value}`;
        }
      }
    });
    
    return cacheKey;
  }

  /**
   * Invalidates specific cache entries by key or prefix
   * 
   * @param keyOrPrefix Cache key or prefix to invalidate
   * @param isPrefix Whether the key is a prefix
   */
  invalidateCache(keyOrPrefix: string, isPrefix: boolean = false): void {
    if (!this.cachingEnabled) return;
    
    if (isPrefix) {
      this.cacheService.clearByPrefix(keyOrPrefix);
    } else {
      this.cacheService.remove(keyOrPrefix);
    }
  }

  /**
   * Builds a complete URL from the API base URL and endpoint
   * 
   * @param endpoint API endpoint path
   * @returns Complete URL
   */
  private buildUrl(endpoint: string): string {
    // Remove leading slash if present to avoid double slashes
    if (endpoint.startsWith('/')) {
      endpoint = endpoint.substring(1);
    }
    
    return `${this.apiUrl}/${endpoint}`;
  }
}