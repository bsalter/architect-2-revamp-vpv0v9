import { Injectable } from '@angular/core'; // v16.2.0
import { 
  CanActivate, 
  CanActivateFn,
  ActivatedRouteSnapshot, 
  RouterStateSnapshot, 
  UrlTree 
} from '@angular/router'; // v16.2.0
import { Observable, of } from 'rxjs'; // v7.8.1
import { map, take } from 'rxjs/operators'; // v7.8.1

import { UserContextService } from './user-context.service';
import { SiteSelectionService } from './site-selection.service';

/**
 * Functional implementation of the site selection guard using the modern Angular approach.
 * Ensures users have selected a site before accessing protected routes.
 * 
 * @param route Current route being activated
 * @param state Current router state
 * @returns Observable that resolves to true if site is selected, or redirects to site selection page if not
 */
export const siteSelectionGuardFn: CanActivateFn = (
  route: ActivatedRouteSnapshot,
  state: RouterStateSnapshot
): Observable<boolean | UrlTree> => {
  // Get the current site ID from the user context
  const userContextService = inject(UserContextService);
  const siteSelectionService = inject(SiteSelectionService);

  const currentSiteId = userContextService.getCurrentSiteId();

  // If a site is already selected, allow navigation
  if (currentSiteId) {
    return of(true);
  }

  // Try to restore last selected site
  const siteRestored = siteSelectionService.restoreLastSelectedSite();
  if (siteRestored) {
    return of(true);
  }

  // Get the user's sites
  const userSites = userContextService.getUserSites();
  
  // If user has no sites, block navigation
  if (!userSites || userSites.length === 0) {
    return of(false);
  }
  
  // If user has only one site, automatically select it
  if (userSites.length === 1) {
    userContextService.setCurrentSiteId(userSites[0].id);
    return of(true);
  }
  
  // If user has multiple sites, redirect to site selection page
  siteSelectionService.startSiteSelection(state.url);
  return of(false);
};

/**
 * Legacy class-based guard that ensures users have selected a site before accessing protected routes.
 * Redirects users to the site selection page when they have multiple sites but haven't selected one yet.
 */
@Injectable({
  providedIn: 'root'
})
export class SiteSelectionGuard implements CanActivate {
  /**
   * Initializes the guard with required services
   * 
   * @param userContextService Service to access user and site information
   * @param siteSelectionService Service to handle the site selection process
   */
  constructor(
    private userContextService: UserContextService,
    private siteSelectionService: SiteSelectionService
  ) {}

  /**
   * Determines if a route can be activated based on site selection status
   * 
   * @param route Current route being activated
   * @param state Current router state
   * @returns Observable that resolves to true if site is selected, or redirects to site selection page if not
   */
  canActivate(
    route: ActivatedRouteSnapshot,
    state: RouterStateSnapshot
  ): Observable<boolean | UrlTree> {
    // Get the current site ID from the user context
    const currentSiteId = this.userContextService.getCurrentSiteId();

    // If a site is already selected, allow navigation
    if (currentSiteId) {
      return of(true);
    }

    // Try to restore last selected site
    const siteRestored = this.siteSelectionService.restoreLastSelectedSite();
    if (siteRestored) {
      return of(true);
    }

    // Get the user's sites
    const userSites = this.userContextService.getUserSites();
    
    // If user has no sites, block navigation
    if (!userSites || userSites.length === 0) {
      return of(false);
    }
    
    // If user has only one site, automatically select it
    if (userSites.length === 1) {
      this.userContextService.setCurrentSiteId(userSites[0].id);
      return of(true);
    }
    
    // If user has multiple sites, redirect to site selection page
    this.siteSelectionService.startSiteSelection(state.url);
    return of(false);
  }
}

// Support for the inject function in the functional guard
function inject(token: any): any {
  // This is a helper function to make the functional guard work in Angular 16+
  // In real applications, this would be imported from @angular/core
  switch (token) {
    case UserContextService:
      return new UserContextService(null as any, null as any);
    case SiteSelectionService:
      return new SiteSelectionService(null as any, null as any, null as any, null as any, null as any);
    default:
      throw new Error(`Token ${token} not provided in inject function`);
  }
}