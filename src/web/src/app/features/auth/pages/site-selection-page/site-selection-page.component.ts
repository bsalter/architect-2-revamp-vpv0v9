import { Component, OnInit, OnDestroy } from '@angular/core'; // @angular/core 16.2.0
import { Router } from '@angular/router'; // @angular/router 16.2.0
import { Subscription, Subject } from 'rxjs'; // rxjs 7.8.1
import { takeUntil } from 'rxjs/operators'; // rxjs/operators 7.8.1

import { SiteSelectionComponent } from '../../components/site-selection/site-selection.component';
import { SiteSelectionService } from '../../../../core/auth/site-selection.service';
import { AuthService } from '../../../../core/auth/auth.service';

/**
 * Page component that hosts the site selection interface and manages the site selection workflow.
 * Displayed after successful authentication when a user has multiple site associations,
 * implementing the site-scoping requirement of the Interaction Management System.
 */
@Component({
  selector: 'app-site-selection-page',
  templateUrl: './site-selection-page.component.html',
  styleUrls: ['./site-selection-page.component.scss']
})
export class SiteSelectionPageComponent implements OnInit, OnDestroy {
  /** Flag indicating if a loading operation is in progress */
  isLoading = false;
  
  /** Subject for managing subscription lifecycle */
  private destroy$ = new Subject<void>();
  
  /** Collection of subscriptions to clean up on component destruction */
  private subscription = new Subscription();

  /**
   * Creates an instance of SiteSelectionPageComponent.
   * Initializes the component with required services.
   * 
   * @param router Angular router for navigation
   * @param siteSelectionService Service for managing site selection workflow
   * @param authService Service for checking authentication status
   */
  constructor(
    private router: Router,
    private siteSelectionService: SiteSelectionService,
    private authService: AuthService
  ) {}

  /**
   * Lifecycle hook that initializes the component and verifies authentication.
   * Checks if site selection is in progress and redirects if not needed.
   */
  ngOnInit(): void {
    // Check if the user is authenticated
    this.authService.isAuthenticated()
      .pipe(takeUntil(this.destroy$))
      .subscribe(isAuthenticated => {
        if (!isAuthenticated) {
          // Redirect to login if not authenticated
          this.router.navigate(['/login']);
          return;
        }
        
        // Subscribe to site selection status to verify it's in progress
        this.subscription.add(
          this.siteSelectionService.siteSelectionInProgress$
            .pipe(takeUntil(this.destroy$))
            .subscribe(inProgress => {
              if (!inProgress) {
                // If site selection is not in progress, redirect to dashboard
                this.router.navigate(['/dashboard']);
              }
            })
        );
      });
  }

  /**
   * Lifecycle hook for cleanup when component is destroyed.
   * Ensures all subscriptions are properly unsubscribed.
   */
  ngOnDestroy(): void {
    // Signal completion to all observables
    this.destroy$.next();
    this.destroy$.complete();
    
    // Unsubscribe from subscription to prevent memory leaks
    this.subscription.unsubscribe();
  }

  /**
   * Handler for when the user confirms site selection.
   * Navigates to the redirect URL provided by the site selection service.
   */
  onSiteSelected(): void {
    // Navigate to the redirect URL from the service
    this.router.navigate([this.siteSelectionService.getRedirectUrl()])
      .catch(error => {
        console.error('Navigation error after site selection:', error);
      });
  }

  /**
   * Handler for when the user cancels site selection.
   * Navigates back to the login page or other designated page.
   */
  onCancel(): void {
    // Navigate to login page
    this.router.navigate(['/login'])
      .catch(error => {
        console.error('Navigation error after canceling site selection:', error);
      });
  }
}