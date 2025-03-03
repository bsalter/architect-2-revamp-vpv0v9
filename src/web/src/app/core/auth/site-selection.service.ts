import { Injectable } from '@angular/core'; // v16.2.0
import { Router } from '@angular/router'; // v16.2.0
import { HttpClient } from '@angular/common/http'; // v16.2.0
import { Observable, BehaviorSubject, of, throwError } from 'rxjs'; // v7.8.1
import { catchError, tap, finalize, map } from 'rxjs/operators'; // v7.8.1

import { User } from './user.model';
import { SiteWithRole } from '../../features/sites/models/site.model';
import { UserContextService } from './user-context.service';
import { CacheService } from '../cache/cache.service';
import * as CacheKeys from '../cache/cache-keys';
import { ErrorHandlerService } from '../errors/error-handler.service';

/**
 * Service responsible for managing the site selection workflow after authentication
 * when users have access to multiple sites. Provides methods to handle the site
 * selection process and maintains the workflow state.
 */
@Injectable({
  providedIn: 'root'
})
export class SiteSelectionService {
  // BehaviorSubject tracking whether site selection is currently in progress
  private siteSelectionInProgressSubject = new BehaviorSubject<boolean>(false);
  public siteSelectionInProgress$ = this.siteSelectionInProgressSubject.asObservable();
  
  // BehaviorSubject tracking loading state during site operations
  private isLoadingSubject = new BehaviorSubject<boolean>(false);
  public isLoading$ = this.isLoadingSubject.asObservable();
  
  // URL to redirect to after site selection is complete
  private redirectUrl: string = '';
  
  // API endpoints related to site selection
  private apiEndpoints = {
    userSites: '/api/users/sites'
  };

  /**
   * Creates an instance of SiteSelectionService.
   * 
   * @param router Angular router for navigation
   * @param userContextService Service for managing user context and site access
   * @param httpClient HTTP client for API requests
   * @param cacheService Service for caching site selection preferences
   * @param errorHandler Service for standardized error handling
   */
  constructor(
    private router: Router,
    private userContextService: UserContextService,
    private httpClient: HttpClient,
    private cacheService: CacheService,
    private errorHandler: ErrorHandlerService
  ) {}

  /**
   * Determines if site selection is required after authentication
   * by checking if the user has access to multiple sites
   * 
   * @returns True if site selection is required, false otherwise
   */
  checkSiteSelectionRequired(): boolean {
    const user = this.userContextService.getCurrentUser();
    
    if (!user) {
      return false; // No authenticated user
    }
    
    const siteIds = user.getSiteIds();
    
    if (siteIds.length === 0) {
      // User has no site access, handle as error
      this.errorHandler.handleError(
        new Error('User has no site access'),
        'SiteSelectionService.checkSiteSelectionRequired'
      );
      return false;
    } else if (siteIds.length === 1) {
      // User has only one site, automatically select it
      this.userContextService.setCurrentSiteId(siteIds[0]);
      return false;
    } else {
      // User has multiple sites, selection is required
      return true;
    }
  }

  /**
   * Initiates the site selection process by storing the redirect URL
   * and navigating to the site selection page
   * 
   * @param redirectAfterSelection URL to redirect to after site selection
   */
  startSiteSelection(redirectAfterSelection: string): void {
    this.redirectUrl = redirectAfterSelection;
    this.siteSelectionInProgressSubject.next(true);
    this.router.navigate(['/auth/site-selection']);
  }

  /**
   * Gets the list of sites available to the current user
   * First tries to get the sites from user context, then falls back to API
   * 
   * @returns Observable of sites with user roles
   */
  getAvailableSites(): Observable<SiteWithRole[]> {
    this.isLoadingSubject.next(true);
    
    // Try to get sites from user context first
    const userSites = this.userContextService.getUserSites();
    
    if (userSites) {
      this.isLoadingSubject.next(false);
      return of(userSites);
    }
    
    // If not available in context, fetch from API
    return this.httpClient.get<SiteWithRole[]>(this.apiEndpoints.userSites).pipe(
      map(response => response),
      catchError(error => {
        this.errorHandler.handleError(
          error,
          'SiteSelectionService.getAvailableSites'
        );
        return throwError(() => error);
      }),
      finalize(() => this.isLoadingSubject.next(false))
    );
  }

  /**
   * Processes the user's site selection and completes the workflow
   * Verifies access, updates context, caches the selection, and redirects
   * 
   * @param siteId The selected site ID
   * @returns Observable that completes when selection is processed
   */
  selectSite(siteId: number): Observable<boolean> {
    this.isLoadingSubject.next(true);
    
    try {
      // Verify user has access to this site
      const user = this.userContextService.getCurrentUser();
      
      if (!user || !user.hasSiteAccess(siteId)) {
        throw new Error('No access to selected site');
      }
      
      // Update the user's current site
      const success = this.userContextService.setCurrentSiteId(siteId);
      
      if (!success) {
        throw new Error('Failed to set current site');
      }
      
      // Cache the site selection for future sessions
      this.cacheService.set(
        CacheKeys.CURRENT_SITE_KEY,
        siteId,
        CacheKeys.SITE_CACHE_DURATION
      );
      
      // Complete the site selection process
      this.siteSelectionInProgressSubject.next(false);
      
      // Navigate to the redirect URL or default dashboard
      const redirectUrl = this.redirectUrl || '/dashboard';
      this.router.navigate([redirectUrl]);
      
      return of(true);
    } catch (error) {
      this.errorHandler.handleError(
        error,
        'SiteSelectionService.selectSite'
      );
      return throwError(() => error);
    } finally {
      this.isLoadingSubject.next(false);
    }
  }

  /**
   * Cancels the site selection process
   * Resets state and navigates away from selection page
   */
  cancelSiteSelection(): void {
    this.siteSelectionInProgressSubject.next(false);
    this.redirectUrl = '';
    // Navigate back to login or home
    this.router.navigate(['/']);
  }

  /**
   * Gets the URL to redirect to after site selection
   * 
   * @returns URL to redirect to or default dashboard path
   */
  getRedirectUrl(): string {
    return this.redirectUrl || '/dashboard';
  }

  /**
   * Attempts to restore the last selected site from cache
   * 
   * @returns True if site was successfully restored, false otherwise
   */
  restoreLastSelectedSite(): boolean {
    try {
      const user = this.userContextService.getCurrentUser();
      
      if (!user) {
        return false;
      }
      
      // Try to get cached site selection
      const cachedSiteId = this.cacheService.get(CacheKeys.CURRENT_SITE_KEY);
      
      if (cachedSiteId && user.hasSiteAccess(cachedSiteId)) {
        // User still has access to the cached site
        return this.userContextService.setCurrentSiteId(cachedSiteId);
      }
      
      return false;
    } catch (error) {
      this.errorHandler.handleError(
        error,
        'SiteSelectionService.restoreLastSelectedSite',
        false
      );
      return false;
    }
  }

  /**
   * Gets the ID of the currently selected site
   * 
   * @returns Current site ID or null if none selected
   */
  getCurrentSiteId(): number | null {
    return this.userContextService.getCurrentSiteId();
  }
}