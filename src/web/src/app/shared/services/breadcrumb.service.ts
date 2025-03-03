import { Injectable } from '@angular/core'; // v16.2.0
import { Router, ActivatedRoute, NavigationEnd, Event, Params } from '@angular/router'; // v16.2.0
import { Title } from '@angular/platform-browser'; // v16.2.0
import { Observable, BehaviorSubject } from 'rxjs'; // v7.8.1
import { filter, map, mergeMap, takeUntil } from 'rxjs/operators'; // v7.8.1

import { UserContextService } from '../../core/auth/user-context.service';

/**
 * Interface representing a breadcrumb item with label and URL
 */
export interface Breadcrumb {
  label: string;
  url: string;
}

/**
 * Service that manages the breadcrumb navigation by tracking route changes and building breadcrumb items
 */
@Injectable({
  providedIn: 'root'
})
export class BreadcrumbService {
  // BehaviorSubject to track and emit breadcrumb changes
  private breadcrumbsSubject = new BehaviorSubject<Breadcrumb[]>([]);
  // Observable that components can subscribe to for breadcrumb updates
  public breadcrumbs$ = this.breadcrumbsSubject.asObservable();

  /**
   * Initializes the breadcrumb service and sets up route change subscription
   * 
   * @param router Angular router service for navigation events
   * @param activatedRoute Current activated route
   * @param titleService Service to update document title
   * @param userContextService Service to access current site information
   */
  constructor(
    private router: Router,
    private activatedRoute: ActivatedRoute,
    private titleService: Title,
    private userContextService: UserContextService
  ) {
    // Subscribe to router events to update breadcrumbs when navigation occurs
    this.router.events.pipe(
      // Only process NavigationEnd events
      filter((event): event is NavigationEnd => event instanceof NavigationEnd),
    ).subscribe(() => {
      // Update breadcrumbs when navigation completes
      this.updateBreadcrumbs();
    });
  }

  /**
   * Builds the breadcrumb array based on the current route hierarchy
   * 
   * @param route Current route to process
   * @param url URL string accumulated from parent routes
   * @param breadcrumbs Current breadcrumbs array being built
   * @returns Array of breadcrumb items
   */
  private buildBreadcrumbs(route: ActivatedRoute, url: string = '', breadcrumbs: Breadcrumb[] = []): Breadcrumb[] {
    // Get the route configuration data
    const data = route.snapshot.data;
    const routeParams = route.snapshot.params;
    
    // Skip if this route should be hidden from breadcrumbs
    if (this.isRouteHidden(data)) {
      // If we have child routes, process them
      if (route.firstChild) {
        return this.buildBreadcrumbs(route.firstChild, url, breadcrumbs);
      }
      return breadcrumbs;
    }
    
    // Get the route URL segment
    const routeUrl = route.snapshot.url.map(segment => segment.path).join('/');
    
    // Build the URL for this route
    const nextUrl = routeUrl ? url + '/' + routeUrl : url;
    
    // Always add Home as the first breadcrumb if we're at the root and breadcrumbs is empty
    if (breadcrumbs.length === 0 && !nextUrl) {
      breadcrumbs.push({
        label: 'Dashboard',
        url: '/'
      });
    }
    
    // Only add breadcrumb if the route has URL segments
    if (routeUrl) {
      // Get the breadcrumb label from route data or generate a default one
      const label = this.getBreadcrumbLabel(data, routeParams, nextUrl);
      
      // Process dynamic labels for specific routes (e.g., with entity IDs)
      const processedLabel = this.processDynamicLabels(nextUrl, label, routeParams);
      
      // Add the breadcrumb to the array
      breadcrumbs.push({
        label: processedLabel,
        url: nextUrl || '/'
      });
    }
    
    // If we have child routes, process them
    if (route.firstChild) {
      return this.buildBreadcrumbs(route.firstChild, nextUrl, breadcrumbs);
    }
    
    // If no more children, return the complete breadcrumbs
    return breadcrumbs;
  }

  /**
   * Updates the breadcrumb items based on the current route
   */
  public updateBreadcrumbs(): void {
    // Get the root route
    const root = this.activatedRoute.root;
    // Build breadcrumbs starting from the root route
    const breadcrumbs = this.buildBreadcrumbs(root);
    
    // Update the breadcrumbs subject
    this.breadcrumbsSubject.next(breadcrumbs);
    
    // Update the page title based on the last breadcrumb
    if (breadcrumbs.length > 0) {
      const pageTitle = breadcrumbs[breadcrumbs.length - 1].label;
      this.titleService.setTitle(`${pageTitle} - Interaction Management`);
    } else {
      this.titleService.setTitle('Interaction Management');
    }
  }

  /**
   * Gets the label for a breadcrumb, supporting dynamic labels from route data
   * 
   * @param data Route data containing breadcrumb configuration
   * @param params Route parameters
   * @param url Current route URL
   * @returns Resolved breadcrumb label
   */
  private getBreadcrumbLabel(data: any, params: Params, url: string): string {
    // Check if route data contains breadcrumb configuration
    if (data && data.breadcrumb) {
      // If breadcrumb is a string, use it directly
      if (typeof data.breadcrumb === 'string') {
        return data.breadcrumb;
      }
      
      // If breadcrumb is a function, call it with route params
      if (typeof data.breadcrumb === 'function') {
        return data.breadcrumb(params, url);
      }
    }
    
    // If no breadcrumb configuration, extract label from the URL
    const urlSegments = url.split('/').filter(segment => segment);
    const lastSegment = urlSegments.length > 0 ? urlSegments[urlSegments.length - 1] : '';
    
    // Format the URL segment to a readable label
    return this.formatUrlSegmentToLabel(lastSegment);
  }

  /**
   * Formats a URL segment to a readable label
   * 
   * @param segment URL segment
   * @returns Formatted label
   */
  private formatUrlSegmentToLabel(segment: string): string {
    if (!segment) {
      return 'Home';
    }
    
    // Replace hyphens and underscores with spaces
    let label = segment.replace(/[-_]/g, ' ');
    
    // Capitalize the first letter of each word
    label = label.replace(/\w\S*/g, (word) => {
      return word.charAt(0).toUpperCase() + word.substring(1).toLowerCase();
    });
    
    return label;
  }

  /**
   * Resolves dynamic breadcrumb labels based on entity IDs and current data
   * 
   * @param url Current route URL
   * @param label Base label to process
   * @param params Route parameters
   * @returns Resolved label with dynamic content
   */
  private processDynamicLabels(url: string, label: string, params: Params): string {
    // Handle interaction routes
    if (url.includes('/interactions/') && params['id']) {
      // For view or edit pages of interactions
      if (url.includes('/edit')) {
        return `Edit Interaction #${params['id']}`;
      } else if (url.includes('/view')) {
        return `Interaction #${params['id']}`;
      }
    }
    
    // Handle site-specific pages
    if (url.includes('/sites/') && params['siteId']) {
      // For site-specific pages, we could enhance this by using the site name
      // from userContextService.currentSite$, but for now, a simple label will do
      return `${label} (Site ${params['siteId']})`;
    }
    
    return label;
  }

  /**
   * Determines if a route should be hidden from breadcrumbs
   * 
   * @param data Route data containing breadcrumb configuration
   * @returns True if route should be hidden from breadcrumbs
   */
  private isRouteHidden(data: any): boolean {
    return data && data.breadcrumb && data.breadcrumb.hide === true;
  }
}