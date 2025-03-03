import { Injectable } from '@angular/core'; // v16.2.0
import { Observable, BehaviorSubject, of } from 'rxjs'; // v7.8.1
import { map } from 'rxjs/operators'; // v7.8.1

import { User, UserRoleEnum } from './user.model';
import { TokenService } from './token.service';
import { SiteWithRole } from '../../../features/sites/models/site.model';
import { CacheService } from '../cache/cache.service';
import * as CacheKeys from '../cache/cache-keys';

/**
 * Service that manages the authenticated user's context, including identity, 
 * site permissions, and current site selection. It provides centralized user 
 * state management with reactive streams for components to consume user 
 * information and permissions.
 * 
 * This service implements the site-scoped access control model specified in the
 * technical requirements, providing methods to check permissions and manage
 * the current user's site context.
 */
@Injectable({
  providedIn: 'root'
})
export class UserContextService {
  // BehaviorSubjects to track user state changes
  private currentUserSubject: BehaviorSubject<User | null> = new BehaviorSubject<User | null>(null);
  public currentUser$: Observable<User | null> = this.currentUserSubject.asObservable();

  // BehaviorSubjects to track site context changes
  private currentSiteIdSubject: BehaviorSubject<number | null> = new BehaviorSubject<number | null>(null);
  public currentSiteId$: Observable<number | null> = this.currentSiteIdSubject.asObservable();

  private currentSiteSubject: BehaviorSubject<SiteWithRole | null> = new BehaviorSubject<SiteWithRole | null>(null);
  public currentSite$: Observable<SiteWithRole | null> = this.currentSiteSubject.asObservable();

  /**
   * Creates an instance of UserContextService.
   * Initializes the user context and attempts to restore state from cache.
   * 
   * @param tokenService Service for token management
   * @param cacheService Service for caching user data
   */
  constructor(
    private tokenService: TokenService,
    private cacheService: CacheService
  ) {
    // Attempt to restore user context from cache during initialization
    this.restoreFromCache();
  }

  /**
   * Sets the current authenticated user and updates relevant observables.
   * 
   * @param user The user object to set as current
   */
  setCurrentUser(user: User): void {
    this.currentUserSubject.next(user);
    
    // Cache the user for persistence across page refreshes
    this.cacheService.set(
      CacheKeys.AUTH_USER_KEY, 
      user, 
      CacheKeys.AUTH_CACHE_DURATION
    );
    
    // If the user has a current site ID set, update site-related observables
    if (user && user.currentSiteId) {
      const currentSite = user.getCurrentSite();
      this.currentSiteIdSubject.next(user.currentSiteId);
      
      if (currentSite) {
        this.currentSiteSubject.next(currentSite);
        // Cache current site selection
        this.cacheService.set(
          CacheKeys.CURRENT_SITE_KEY, 
          user.currentSiteId, 
          CacheKeys.SITE_CACHE_DURATION
        );
      }
    }
  }

  /**
   * Gets the current authenticated user.
   * 
   * @returns The current user or null if not authenticated
   */
  getCurrentUser(): User | null {
    return this.currentUserSubject.value;
  }

  /**
   * Clears all user context data when logging out.
   */
  clearUserContext(): void {
    this.currentUserSubject.next(null);
    this.currentSiteIdSubject.next(null);
    this.currentSiteSubject.next(null);
    
    // Remove cached user data
    this.cacheService.remove(CacheKeys.AUTH_USER_KEY);
    this.cacheService.remove(CacheKeys.CURRENT_SITE_KEY);
  }

  /**
   * Refreshes user context from the current JWT token.
   * 
   * @returns Updated user object or null if token invalid
   */
  refreshUserFromToken(): User | null {
    const token = this.tokenService.getToken();
    if (!token) {
      return null;
    }
    
    const user = this.tokenService.getUserFromToken(token);
    if (user) {
      this.setCurrentUser(user);
    }
    
    return user;
  }

  /**
   * Sets the current active site for the user context.
   * 
   * @param siteId The site ID to set as current
   * @returns True if site was set successfully, false otherwise
   */
  setCurrentSiteId(siteId: number): boolean {
    const user = this.getCurrentUser();
    if (!user) {
      return false;
    }
    
    // Verify user has access to this site
    if (!user.hasSiteAccess(siteId)) {
      return false;
    }
    
    // Update user's current site
    const success = user.setCurrentSite(siteId);
    if (!success) {
      return false;
    }
    
    // Update the site-related observables
    this.currentSiteIdSubject.next(siteId);
    
    // Update the current site with role
    const currentSite = user.getCurrentSite();
    if (currentSite) {
      this.currentSiteSubject.next(currentSite);
    }
    
    // Cache the site selection
    this.cacheService.set(
      CacheKeys.CURRENT_SITE_KEY, 
      siteId, 
      CacheKeys.SITE_CACHE_DURATION
    );
    
    return true;
  }

  /**
   * Gets the ID of the currently selected site.
   * 
   * @returns Current site ID or null if none selected
   */
  getCurrentSiteId(): number | null {
    return this.currentSiteIdSubject.value;
  }

  /**
   * Checks if the current user has access to a specific site.
   * 
   * @param siteId The site ID to check access for
   * @returns True if user has access to the specified site
   */
  hasSiteAccess(siteId: number): boolean {
    const user = this.getCurrentUser();
    if (!user) {
      return false;
    }
    
    return user.hasSiteAccess(siteId);
  }

  /**
   * Checks if the current user has a specific role or higher for the current or specified site.
   * 
   * @param requiredRole The minimum role required (from UserRoleEnum)
   * @param siteId Optional site ID, uses current site if not provided
   * @returns True if user has the required role or higher
   */
  hasPermission(requiredRole: string, siteId: number | null = null): boolean {
    const user = this.getCurrentUser();
    if (!user) {
      return false;
    }
    
    // If no site ID provided, use current site
    const targetSiteId = siteId || this.getCurrentSiteId();
    if (!targetSiteId) {
      return false;
    }
    
    return user.hasRoleForSite(targetSiteId, requiredRole);
  }

  /**
   * Checks if the current user has admin role for the current or specified site.
   * 
   * @param siteId Optional site ID, uses current site if not provided
   * @returns True if user has admin role
   */
  isAdmin(siteId: number | null = null): boolean {
    return this.hasPermission(UserRoleEnum.SITE_ADMIN, siteId);
  }

  /**
   * Checks if the current user has editor role (or higher) for the current or specified site.
   * 
   * @param siteId Optional site ID, uses current site if not provided
   * @returns True if user has editor role or higher
   */
  isEditor(siteId: number | null = null): boolean {
    return this.hasPermission(UserRoleEnum.EDITOR, siteId);
  }

  /**
   * Checks if the current user has at least viewer role for the current or specified site.
   * 
   * @param siteId Optional site ID, uses current site if not provided
   * @returns True if user has at least viewer role
   */
  isViewer(siteId: number | null = null): boolean {
    return this.hasPermission(UserRoleEnum.VIEWER, siteId);
  }

  /**
   * Attempts to restore user context from cache.
   * 
   * @returns True if context successfully restored
   */
  restoreFromCache(): boolean {
    try {
      // Try to get cached user data
      const cachedUser = this.cacheService.get(CacheKeys.AUTH_USER_KEY);
      
      if (cachedUser) {
        // Reconstruct User object from cached data
        const user = new User(cachedUser);
        this.currentUserSubject.next(user);
        
        // Try to restore site selection
        const cachedSiteId = this.cacheService.get(CacheKeys.CURRENT_SITE_KEY);
        
        if (cachedSiteId && user.hasSiteAccess(cachedSiteId)) {
          user.setCurrentSite(cachedSiteId);
          this.currentSiteIdSubject.next(cachedSiteId);
          
          const currentSite = user.getCurrentSite();
          if (currentSite) {
            this.currentSiteSubject.next(currentSite);
          }
        } else if (user.sites.length > 0) {
          // Default to first available site
          const firstSiteId = user.sites[0].id;
          user.setCurrentSite(firstSiteId);
          this.currentSiteIdSubject.next(firstSiteId);
          this.currentSiteSubject.next(user.sites[0]);
        }
        
        return true;
      }
      
      return false;
    } catch (error) {
      console.error('Error restoring user context from cache:', error);
      return false;
    }
  }

  /**
   * Gets the list of sites that the current user has access to.
   * 
   * @returns Array of sites with roles or null if not authenticated
   */
  getUserSites(): SiteWithRole[] | null {
    const user = this.getCurrentUser();
    if (!user) {
      return null;
    }
    
    return user.sites;
  }
}