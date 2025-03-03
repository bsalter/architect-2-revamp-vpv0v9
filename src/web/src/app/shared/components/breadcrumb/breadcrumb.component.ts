import { Component, OnInit, OnDestroy } from '@angular/core'; // v16.2.0
import { Router } from '@angular/router'; // v16.2.0
import { Subject } from 'rxjs'; // v7.8.1
import { takeUntil } from 'rxjs/operators'; // v7.8.1

import { BreadcrumbService } from '../../services/breadcrumb.service';
import { UserContextService } from '../../../core/auth/user-context.service';

/**
 * Component that displays a hierarchical breadcrumb navigation trail showing 
 * the user's current position in the application.
 * 
 * Features:
 * - Shows the current navigation path as clickable links
 * - Updates automatically when routes change
 * - Adapts to site context changes
 * - Provides accessible navigation with proper ARIA attributes
 */
@Component({
  selector: 'app-breadcrumb',
  templateUrl: './breadcrumb.component.html',
  styleUrls: ['./breadcrumb.component.scss']
})
export class BreadcrumbComponent implements OnInit, OnDestroy {
  /**
   * Whether to show the home link as the first breadcrumb
   */
  showHome = true;
  
  /**
   * Subject used to handle unsubscribing from observables when component is destroyed
   */
  private destroy$ = new Subject<void>();

  /**
   * Initializes the breadcrumb component with required services
   * 
   * @param breadcrumbService Service providing breadcrumb data stream
   * @param router Angular router for navigation
   * @param userContextService Service providing current site information
   */
  constructor(
    public breadcrumbService: BreadcrumbService,
    private router: Router,
    private userContextService: UserContextService
  ) { }

  /**
   * Lifecycle hook that initializes the component and subscribes to site changes
   * and breadcrumb updates.
   */
  ngOnInit(): void {
    // Subscribe to site changes to update breadcrumbs when site context changes
    this.userContextService.currentSite$
      .pipe(takeUntil(this.destroy$))
      .subscribe(site => {
        if (site) {
          // Trigger breadcrumb service to update with new site context
          this.breadcrumbService.updateBreadcrumbs();
        }
      });
  }

  /**
   * Lifecycle hook that cleans up subscriptions when component is destroyed
   */
  ngOnDestroy(): void {
    // Emit value to trigger all takeUntil operators
    this.destroy$.next();
    // Complete the subject to free resources
    this.destroy$.complete();
  }

  /**
   * Handles breadcrumb link click and navigates to the specified URL
   * 
   * @param url The destination URL to navigate to
   * @param event The mouse event from the click
   */
  navigateTo(url: string, event: MouseEvent): void {
    // Prevent default browser navigation
    event.preventDefault();
    
    // Use Angular router to navigate
    this.router.navigateByUrl(url)
      .catch(error => {
        console.error('Navigation error:', error);
      });
  }
}