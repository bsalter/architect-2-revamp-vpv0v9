import { Injectable } from '@angular/core'; // v16.2.0
import { Observable, BehaviorSubject, of, throwError } from 'rxjs'; // v7.8.1
import { catchError, tap, map, shareReplay } from 'rxjs/operators'; // v7.8.1

import { ApiService } from '../../../core/http/api.service';
import { UserContextService } from '../../../core/auth/user-context.service';
import { CacheService } from '../../../core/cache/cache.service';
import * as CacheKeys from '../../../core/cache/cache-keys';
import { 
  Site, 
  SiteWithRole, 
  SiteOption, 
  SiteListResponse, 
  SiteCreate, 
  SiteUpdate 
} from '../models/site.model';

/**
 * Service that provides methods for retrieving and managing site data, supporting the site-scoped
 * architecture of the application. This service is critical for implementing the multi-tenant
 * nature of the Interaction Management System by enforcing site-based access control.
 */
@Injectable({
  providedIn: 'root'
})
export class SiteService {
  // BehaviorSubjects for site data and loading state
  private sitesSubject: BehaviorSubject<SiteOption[]> = new BehaviorSubject<SiteOption[]>([]);
  public sites$: Observable<SiteOption[]> = this.sitesSubject.asObservable().pipe(shareReplay(1));
  
  private loadingSubject: BehaviorSubject<boolean> = new BehaviorSubject<boolean>(false);
  public loading$: Observable<boolean> = this.loadingSubject.asObservable();
  
  // API endpoints for site-related operations
  private apiEndpoints = {
    sites: 'sites',
    userSites: 'users/sites',
    siteOptions: 'sites/options'
  };

  /**
   * Initializes the site service with required dependencies
   * 
   * @param apiService Service for making API requests
   * @param userContextService Service for accessing user context and site permissions
   * @param cacheService Service for caching site data
   */
  constructor(
    private apiService: ApiService,
    private userContextService: UserContextService,
    private cacheService: CacheService
  ) {}

  /**
   * Gets simplified site options for dropdowns and selectors
   * 
   * @param forceRefresh Whether to bypass cache and force a refresh from the API
   * @returns Observable of available site options
   */
  getSiteOptions(forceRefresh: boolean = false): Observable<SiteOption[]> {
    // If we already have loaded sites and don't need to refresh, return existing data
    if (this.sitesSubject.value.length > 0 && !forceRefresh) {
      return this.sites$;
    }
    
    this.loadingSubject.next(true);
    
    // Try to get from cache if not forcing refresh
    if (!forceRefresh) {
      const cachedOptions = this.cacheService.get(CacheKeys.SITES_LIST_KEY);
      if (cachedOptions) {
        this.sitesSubject.next(cachedOptions);
        this.loadingSubject.next(false);
        return this.sites$;
      }
    }
    
    // Otherwise fetch from API
    return this.apiService.get<SiteOption[]>(this.apiEndpoints.siteOptions).pipe(
      map(response => {
        this.sitesSubject.next(response);
        // Cache the results
        this.cacheService.set(
          CacheKeys.SITES_LIST_KEY, 
          response, 
          CacheKeys.SITE_CACHE_DURATION
        );
        return response;
      }),
      catchError(error => {
        return throwError(() => new Error('Failed to load site options. Please try again later.'));
      }),
      tap(() => this.loadingSubject.next(false))
    );
  }

  /**
   * Gets the list of sites that the current user has access to
   * 
   * @param includeRoles Whether to include user roles in the response
   * @returns Observable of sites with user roles
   */
  getUserSites(includeRoles: boolean = true): Observable<SiteWithRole[]> {
    this.loadingSubject.next(true);
    
    const params = includeRoles ? { include_roles: true } : {};
    
    return this.apiService.get<SiteWithRole[]>(this.apiEndpoints.userSites, params).pipe(
      map(response => response),
      catchError(error => {
        return throwError(() => new Error('Failed to load your accessible sites. Please try again later.'));
      }),
      tap(() => this.loadingSubject.next(false))
    );
  }

  /**
   * Gets details of a specific site by ID
   * 
   * @param siteId ID of the site to retrieve
   * @param useCache Whether to use cached data if available
   * @returns Observable with site details
   */
  getSite(siteId: number, useCache: boolean = true): Observable<Site> {
    // Verify the user has access to this site
    if (!this.userContextService.hasSiteAccess(siteId)) {
      return throwError(() => new Error('You do not have access to this site.'));
    }
    
    // Generate cache key for this site
    const cacheKey = `${CacheKeys.SITE_DETAIL_KEY_PREFIX}${siteId}`;
    
    // Try to get from cache if using cache
    if (useCache) {
      const cachedSite = this.cacheService.get(cacheKey);
      if (cachedSite) {
        return of(cachedSite);
      }
    }
    
    return this.apiService.get<Site>(`${this.apiEndpoints.sites}/${siteId}`).pipe(
      tap(site => {
        // Cache the site details
        if (useCache) {
          this.cacheService.set(
            cacheKey, 
            site, 
            CacheKeys.SITE_CACHE_DURATION
          );
        }
      }),
      catchError(error => {
        return throwError(() => new Error('Failed to load site details. Please try again later.'));
      })
    );
  }

  /**
   * Gets a paginated list of all sites (admin function)
   * 
   * @param page Page number to retrieve
   * @param pageSize Number of items per page
   * @param filters Optional filter criteria
   * @returns Observable with paginated site list
   */
  getAllSites(page: number = 1, pageSize: number = 10, filters: object = {}): Observable<SiteListResponse> {
    this.loadingSubject.next(true);
    
    // Prepare query parameters
    const params = {
      page,
      page_size: pageSize,
      ...filters
    };
    
    return this.apiService.get<SiteListResponse>(this.apiEndpoints.sites, params).pipe(
      map(response => response),
      catchError(error => {
        return throwError(() => new Error('Failed to load sites. Please try again later.'));
      }),
      tap(() => this.loadingSubject.next(false))
    );
  }

  /**
   * Creates a new site (admin function)
   * 
   * @param siteData Site data for creation
   * @returns Observable with created site
   */
  createSite(siteData: SiteCreate): Observable<Site> {
    // Validate required fields
    if (!siteData.name) {
      return throwError(() => new Error('Site name is required.'));
    }
    
    this.loadingSubject.next(true);
    
    return this.apiService.post<Site>(this.apiEndpoints.sites, siteData).pipe(
      tap(() => {
        // Invalidate site-related caches on success
        this.invalidateSiteCaches();
      }),
      catchError(error => {
        return throwError(() => new Error('Failed to create site. Please try again later.'));
      }),
      tap(() => this.loadingSubject.next(false))
    );
  }

  /**
   * Updates an existing site (admin function)
   * 
   * @param siteId ID of the site to update
   * @param siteData Updated site data
   * @returns Observable with updated site
   */
  updateSite(siteId: number, siteData: SiteUpdate): Observable<Site> {
    // Validate site ID and admin access
    if (!siteId) {
      return throwError(() => new Error('Site ID is required.'));
    }
    
    // Check for admin permission
    if (!this.userContextService.isAdmin(siteId)) {
      return throwError(() => new Error('You do not have permission to update this site.'));
    }
    
    this.loadingSubject.next(true);
    
    return this.apiService.put<Site>(`${this.apiEndpoints.sites}/${siteId}`, siteData).pipe(
      tap(() => {
        // Invalidate site caches on successful update
        this.invalidateSiteCaches();
      }),
      catchError(error => {
        return throwError(() => new Error('Failed to update site. Please try again later.'));
      }),
      tap(() => this.loadingSubject.next(false))
    );
  }

  /**
   * Deletes a site (admin function)
   * 
   * @param siteId ID of the site to delete
   * @returns Observable with deletion result
   */
  deleteSite(siteId: number): Observable<boolean> {
    // Validate site ID and admin access
    if (!siteId) {
      return throwError(() => new Error('Site ID is required.'));
    }
    
    // Check for admin permission
    if (!this.userContextService.isAdmin(siteId)) {
      return throwError(() => new Error('You do not have permission to delete this site.'));
    }
    
    this.loadingSubject.next(true);
    
    return this.apiService.delete<any>(`${this.apiEndpoints.sites}/${siteId}`).pipe(
      map(() => true), // Return true for successful deletion
      tap(() => {
        // Invalidate all site-related caches on successful deletion
        this.invalidateSiteCaches();
      }),
      catchError(error => {
        return throwError(() => new Error('Failed to delete site. Please try again later.'));
      }),
      tap(() => this.loadingSubject.next(false))
    );
  }

  /**
   * Gets the name of a site by ID
   * 
   * @param siteId ID of the site
   * @returns Observable with site name
   */
  getSiteName(siteId: number): Observable<string> {
    if (!siteId) {
      return of('');
    }
    
    // Check if site options are already loaded
    const sites = this.sitesSubject.value;
    if (sites.length > 0) {
      const site = sites.find(site => site.id === siteId);
      if (site) {
        return of(site.name);
      }
    }
    
    // If not loaded, fetch the individual site
    return this.getSite(siteId).pipe(
      map(site => site.name),
      catchError(() => of(`Site #${siteId}`)) // Fallback name if site can't be loaded
    );
  }

  /**
   * Gets the name of the current active site
   * 
   * @returns Observable with current site name
   */
  getCurrentSiteName(): Observable<string> {
    const currentSiteId = this.userContextService.getCurrentSiteId();
    if (!currentSiteId) {
      return of('');
    }
    
    return this.getSiteName(currentSiteId);
  }

  /**
   * Gets usage statistics for a site
   * 
   * @param siteId ID of the site to get statistics for
   * @returns Observable with site statistics
   */
  getSiteStats(siteId: number): Observable<object> {
    // Validate site ID and access
    if (!siteId) {
      return throwError(() => new Error('Site ID is required.'));
    }
    
    if (!this.userContextService.hasSiteAccess(siteId)) {
      return throwError(() => new Error('You do not have access to this site.'));
    }
    
    this.loadingSubject.next(true);
    
    return this.apiService.get<object>(`${this.apiEndpoints.sites}/${siteId}/stats`).pipe(
      catchError(error => {
        return throwError(() => new Error('Failed to load site statistics. Please try again later.'));
      }),
      tap(() => this.loadingSubject.next(false))
    );
  }

  /**
   * Invalidates all site-related caches
   */
  invalidateSiteCaches(): void {
    // Invalidate cache by prefix using the ApiService
    this.apiService.invalidateCache(CacheKeys.PREFIX_SITE, true);
    this.apiService.invalidateCache(CacheKeys.PREFIX_USER_SITES, true);
    
    // Also explicitly remove site list cache
    this.cacheService.remove(CacheKeys.SITES_LIST_KEY);
    
    // Clear site details caches
    // We rely on the prefix-based invalidation for the detail caches
  }
}