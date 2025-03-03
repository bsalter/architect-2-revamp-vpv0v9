import { Component, OnInit, OnDestroy } from '@angular/core'; // v16.2.0
import { Router, NavigationEnd, ActivatedRoute } from '@angular/router'; // v16.2.0
import { Title } from '@angular/platform-browser'; // v16.2.0
import { Subscription, combineLatest, filter, takeUntil, Subject } from 'rxjs'; // v7.8.1

import { AuthService } from './core/auth/auth.service';
import { SiteSelectionService } from './core/auth/site-selection.service';
import { ToastService } from './shared/services/toast.service';
import { environment } from '../environments/environment';

/**
 * Root component for the Interaction Management System application.
 * Handles application initialization, authentication state management,
 * site context handling, and rendering the main application layout.
 */
@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent implements OnInit, OnDestroy {
  /** Flag indicating whether user is authenticated */
  isAuthenticated = false;
  
  /** Flag indicating whether app is in a loading state */
  isLoading = true;
  
  /** Application version from environment settings */
  appVersion: string;
  
  /** Application title for document title */
  appTitle = 'Interaction Management';
  
  /** Subject for managing subscription cleanup */
  private destroy$ = new Subject<void>();
  
  /** Subscription to router events */
  private routerSub: Subscription;

  /**
   * Creates an instance of AppComponent.
   * 
   * @param router Angular router for navigation events
   * @param route Activated route for title extraction
   * @param authService Service for managing authentication
   * @param siteSelectionService Service for managing site selection
   * @param toastService Service for displaying notifications
   * @param titleService Service for managing document title
   */
  constructor(
    private router: Router,
    private route: ActivatedRoute,
    private authService: AuthService,
    private siteSelectionService: SiteSelectionService,
    private toastService: ToastService,
    private titleService: Title
  ) {
    // Set application version from environment
    this.appVersion = environment.appVersion || '1.0.0';
  }

  /**
   * Lifecycle hook that initializes the component.
   * Sets up subscriptions to router events, authentication state,
   * and loading state tracking.
   */
  ngOnInit(): void {
    // Set up router events subscription for title updates
    this.routerSub = this.router.events.pipe(
      filter(event => event instanceof NavigationEnd),
      takeUntil(this.destroy$)
    ).subscribe(() => {
      this.updateTitle();
    });

    // Set up loading state tracking
    this.setupLoadingState();

    // Check for Auth0 callback in URL
    this.handleAuthCallback();

    // Set up authentication state subscription
    this.setupAuthenticationState();

    // Set initial document title
    this.titleService.setTitle(this.appTitle);
  }

  /**
   * Lifecycle hook that performs cleanup when component is destroyed.
   * Completes the destroy$ subject and unsubscribes from router events.
   */
  ngOnDestroy(): void {
    // Complete the subject to unsubscribe all takeUntil subscriptions
    this.destroy$.next();
    this.destroy$.complete();
    
    // Unsubscribe from router events
    if (this.routerSub) {
      this.routerSub.unsubscribe();
    }
  }

  /**
   * Handles Auth0 redirect callback after successful authentication.
   * Checks URL for callback parameters and processes authentication if present.
   */
  private handleAuthCallback(): void {
    // Check if URL contains Auth0 callback parameters
    if (window.location.search.includes('code=') && 
        window.location.search.includes('state=')) {
      
      // Process the Auth0 callback
      this.authService.handleRedirectCallback()
        .subscribe({
          next: () => {
            if (!environment.production) {
              console.log('Successfully handled Auth0 callback');
            }
          },
          error: (error) => {
            this.toastService.showError('Authentication error. Please try again.');
            console.error('Auth callback error:', error);
          }
        });
    }
  }

  /**
   * Sets up subscription to authentication state.
   * Updates isAuthenticated property and handles site selection when authenticated.
   */
  private setupAuthenticationState(): void {
    this.authService.isAuthenticated()
      .pipe(takeUntil(this.destroy$))
      .subscribe(isAuthenticated => {
        this.isAuthenticated = isAuthenticated;
        
        if (isAuthenticated) {
          // When authenticated, attempt to restore last selected site
          this.siteSelectionService.restoreLastSelectedSite();
        }
        
        if (!environment.production) {
          console.log('Authentication state:', isAuthenticated ? 'Authenticated' : 'Not authenticated');
        }
      });
  }

  /**
   * Sets up subscription to track global loading state.
   * Combines loading indicators from auth service and site selection service.
   */
  private setupLoadingState(): void {
    // Combine observables from auth and site selection services
    combineLatest([
      this.authService.isInitialized$,
      this.authService.isAuthenticating$,
      this.siteSelectionService.siteSelectionInProgress$
    ])
    .pipe(takeUntil(this.destroy$))
    .subscribe(([isInitialized, isAuthenticating, siteSelectionInProgress]) => {
      // Application is loading if auth is not initialized, authentication is in progress,
      // or site selection is in progress
      this.isLoading = !isInitialized || isAuthenticating || siteSelectionInProgress;
    });
  }

  /**
   * Updates the document title based on route data.
   * Traverses the route tree to find the most specific title.
   */
  private updateTitle(): void {
    let routeTitle = '';
    let currentRoute = this.route.root;
    
    // Traverse route tree to find title
    while (currentRoute) {
      if (currentRoute.firstChild) {
        currentRoute = currentRoute.firstChild;
      } else {
        break;
      }
      
      // Get title from route data if available
      if (currentRoute.snapshot.data && currentRoute.snapshot.data['title']) {
        routeTitle = currentRoute.snapshot.data['title'];
      }
    }
    
    // Set document title with route-specific information
    if (routeTitle) {
      this.titleService.setTitle(`${routeTitle} - ${this.appTitle}`);
    } else {
      this.titleService.setTitle(this.appTitle);
    }
  }
}