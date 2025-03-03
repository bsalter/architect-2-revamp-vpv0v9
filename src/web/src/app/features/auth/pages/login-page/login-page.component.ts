import { Component, OnInit, OnDestroy } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
import { Subject } from 'rxjs';
import { filter, takeUntil } from 'rxjs/operators';

import { LoginComponent } from '../../components/login/login.component';
import { AuthService } from '../../../../core/auth/auth.service';
import { AuthPageService } from '../../services/auth-page.service';
import { SiteSelectionService } from '../../../../core/auth/site-selection.service';
import { ToastService } from '../../../../shared/services/toast.service';

/**
 * Container component for the login page that manages authentication flow including redirect handling
 */
@Component({
  selector: 'app-login-page',
  templateUrl: './login-page.component.html',
  styleUrls: ['./login-page.component.scss']
})
export class LoginPageComponent implements OnInit, OnDestroy {
  /** Flag to indicate if the page is in loading state */
  isLoading: boolean = true;
  
  /** Flag to indicate if an authentication callback is being processed */
  isProcessingCallback: boolean = false;
  
  /** Subject for managing unsubscription when component is destroyed */
  private destroy$ = new Subject<void>();
  
  /** URL to return to after successful login */
  returnUrl: string = '';

  /**
   * Initializes the login page component with required services
   * 
   * @param authService Service for authentication operations
   * @param authPageService Service for login page functionality
   * @param siteSelectionService Service for site selection workflow
   * @param router Angular router for navigation
   * @param route Current activated route for query parameters
   * @param toastService Service for displaying notifications
   */
  constructor(
    private authService: AuthService,
    private authPageService: AuthPageService,
    private siteSelectionService: SiteSelectionService,
    private router: Router,
    private route: ActivatedRoute,
    private toastService: ToastService
  ) {
    this.isLoading = true;
    this.isProcessingCallback = false;
    this.destroy$ = new Subject<void>();
  }

  /**
   * Lifecycle hook that initializes component and checks for authentication callback
   */
  ngOnInit(): void {
    // Extract returnUrl from query parameters
    this.returnUrl = this.route.snapshot.queryParams['returnUrl'] || '/dashboard';
    
    // Wait for Auth0 client to be initialized before proceeding
    this.authService.isInitialized$
      .pipe(
        filter(initialized => initialized),
        takeUntil(this.destroy$)
      )
      .subscribe(() => {
        // Check if this is an authentication callback from Auth0
        this.authPageService.checkAndHandleAuthRedirect()
          .pipe(takeUntil(this.destroy$))
          .subscribe({
            next: (callbackHandled) => {
              this.isProcessingCallback = callbackHandled;
              
              // If no callback is being handled, check if user is already authenticated
              if (!callbackHandled) {
                this.checkAuthenticationAndRedirect();
              }
              
              // Update loading state
              this.isLoading = false;
            },
            error: (error) => {
              this.handleError(error);
            }
          });
      });
  }

  /**
   * Lifecycle hook that cleans up subscriptions when component is destroyed
   */
  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * Checks if user is already authenticated and redirects appropriately
   */
  private checkAuthenticationAndRedirect(): void {
    this.authService.isAuthenticated()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (isAuthenticated) => {
          if (isAuthenticated) {
            // User is already authenticated, determine where to navigate
            if (this.siteSelectionService.checkSiteSelectionRequired()) {
              // User has access to multiple sites, start site selection
              this.siteSelectionService.startSiteSelection(this.returnUrl);
            } else {
              // User has access to only one site, navigate directly
              this.router.navigateByUrl(this.returnUrl);
            }
          }
        },
        error: (error) => this.handleError(error)
      });
  }

  /**
   * Handles authentication and navigation errors
   * 
   * @param error The error object
   */
  private handleError(error: Error): void {
    console.error('Login page error:', error);
    
    // Show user-friendly error message
    this.toastService.showError(
      'An error occurred during authentication. Please try again.'
    );
    
    // Reset loading states
    this.isLoading = false;
    this.isProcessingCallback = false;
  }
}