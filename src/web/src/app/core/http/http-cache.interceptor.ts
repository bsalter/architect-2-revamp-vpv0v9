import { Injectable } from '@angular/core'; // v16.2.0
import { 
  HttpInterceptor, 
  HttpRequest, 
  HttpResponse, 
  HttpHandler, 
  HttpEvent 
} from '@angular/common/http'; // v16.2.0
import { Observable, of } from 'rxjs'; // v7.8.1
import { tap } from 'rxjs/operators'; // v7.8.1

import { CacheService } from '../cache/cache.service';
import { environment } from '../../../environments/environment';
import * as CacheKeys from '../cache/cache-keys';

/**
 * HTTP interceptor that implements response caching to improve application performance.
 * This interceptor works with the CacheService to store and retrieve cached responses
 * based on request URLs and query parameters, respecting TTL settings and cache 
 * invalidation rules.
 */
@Injectable()
export class HttpCacheInterceptor implements HttpInterceptor {
  /** Flag indicating if caching is enabled globally */
  private enabled: boolean;
  
  /** Default time-to-live for cached responses in milliseconds */
  private defaultTtl: number;
  
  /** Paths that should be excluded from caching */
  private excludedPaths: string[];
  
  /** HTTP methods that can be cached */
  private cacheableMethods: string[];

  /**
   * Initializes the HTTP cache interceptor with required dependencies
   * 
   * @param cacheService - Service for caching operations
   */
  constructor(private cacheService: CacheService) {
    // Initialize from environment configuration
    this.enabled = environment.caching.enabled;
    this.defaultTtl = environment.caching.defaultTtl * 1000; // Convert seconds to milliseconds
    
    // Define cacheable methods - typically only GET requests are cached
    this.cacheableMethods = ['GET'];
    
    // Define paths that should never be cached
    this.excludedPaths = [
      'auth/', 
      'users/profile',
      'login',
      'logout',
      'token'
    ];
  }

  /**
   * Intercepts HTTP requests and implements response caching
   * 
   * @param request - The outgoing HTTP request
   * @param next - The next handler in the chain
   * @returns Observable of HTTP events
   */
  intercept(request: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    // Skip caching if disabled or method is not cacheable
    if (!this.shouldCache(request)) {
      return next.handle(request);
    }
    
    // Check for cache control headers or query params that bypass cache
    const headerNoCache = request.headers.get('Cache-Control') === 'no-cache';
    const paramNoCache = request.params.get('cache') === 'false';
    
    if (headerNoCache || paramNoCache) {
      return next.handle(request);
    }
    
    // Generate a cache key for this request
    const cacheKey = this.generateCacheKey(request);
    
    // Check if we have a cached response
    const cachedResponse = this.cacheService.get(cacheKey);
    if (cachedResponse) {
      // Return cached response as an observable
      return of(new HttpResponse({
        body: cachedResponse.body,
        headers: cachedResponse.headers,
        status: 200,
        statusText: 'OK',
        url: request.url
      }));
    }
    
    // If no cached response, pass the request to the next handler
    // When the response comes back, cache it before returning
    return next.handle(request).pipe(
      tap(event => {
        if (event instanceof HttpResponse && event.status === 200) {
          try {
            const ttl = this.getTtlForRequest(request);
            this.cacheService.set(cacheKey, event, ttl);
          } catch (error) {
            console.error('Error caching response:', error);
            // Continue even if caching fails
          }
        }
      })
    );
  }

  /**
   * Determines if a request should be cached based on its method and path
   * 
   * @param request - The HTTP request to evaluate
   * @returns True if the request should be cached
   */
  private shouldCache(request: HttpRequest<any>): boolean {
    // Check if caching is enabled globally
    if (!this.enabled) {
      return false;
    }
    
    // Only cache requests with cacheable methods (typically GET)
    if (!this.cacheableMethods.includes(request.method)) {
      return false;
    }
    
    // Don't cache excluded paths
    if (this.shouldExcludePath(request.url)) {
      return false;
    }
    
    return true;
  }

  /**
   * Determines if a request URL should be excluded from caching
   * 
   * @param url - The URL to evaluate
   * @returns True if the path should be excluded
   */
  private shouldExcludePath(url: string): boolean {
    return this.excludedPaths.some(path => url.includes(path));
  }

  /**
   * Generates a unique cache key for a request
   * 
   * @param request - The HTTP request
   * @returns Cache key string
   */
  private generateCacheKey(request: HttpRequest<any>): string {
    // Start with the URL as the base for the cache key
    let key = request.url;
    
    // Append query parameters to the key
    const paramKeys = request.params.keys();
    if (paramKeys.length > 0) {
      // Sort keys to ensure consistent ordering
      const sortedKeys = paramKeys.sort();
      const paramStrings = sortedKeys.map(k => {
        const value = request.params.getAll(k);
        return `${k}=${value.join(',')}`;
      });
      key += `?${paramStrings.join('&')}`;
    }
    
    return key;
  }

  /**
   * Determines the appropriate TTL for a given request
   * 
   * @param request - The HTTP request
   * @returns TTL in milliseconds
   */
  private getTtlForRequest(request: HttpRequest<any>): number {
    const url = request.url.toLowerCase();
    
    // Determine TTL based on the URL path
    if (url.includes('/interactions/') || url.includes('/interactions')) {
      return CacheKeys.INTERACTION_CACHE_DURATION;
    } else if (url.includes('/search')) {
      return CacheKeys.SEARCH_CACHE_DURATION;
    }
    
    // Default TTL for other requests
    return this.defaultTtl;
  }
}