import { Component, OnInit, OnDestroy } from '@angular/core'; // v16.2.0
import { Router } from '@angular/router'; // v16.2.0
import { Observable, Subscription } from 'rxjs'; // v7.8.1
import { take } from 'rxjs/operators'; // v7.8.1

import { AuthService } from '../../../core/auth/auth.service';
import { UserContextService } from '../../../core/auth/user-context.service';
import { SiteSelectionService } from '../../../core/auth/site-selection.service';
import { User } from '../../../core/auth/user.model';
import { SiteWithRole } from '../../../features/sites/models/site.model';

/**
 * Main navigation component that provides the navigation interface for the application.
 * Displays site context, user authentication status, and menu items with
 * proper authorization checks.
 */
@Component({
  selector: 'app-navigation',
  templateUrl: './navigation.component.html',
  styleUrls: ['./navigation.component.scss']
})
export class NavigationComponent implements OnInit, OnDestroy {
  // User and authentication state
  currentUser: User | null = null;
  currentSite: SiteWithRole | null = null;
  isAuthenticated: boolean = false;
  
  // UI state
  isExpanded: boolean = false;
  isMobile: boolean = false;
  
  // Permission flags
  isAdmin: boolean = false;
  isEditor: boolean = false;
  hasSiteAccess: boolean = false;
  hasMultipleSites: boolean = false;
  
  // Subscription collection for cleanup
  subscriptions: Subscription = new Subscription();

  /**
   * Initializes the component with required services
   * 
   * @param authService Service for authentication operations
   * @param userContextService Service for user and site context
   * @param siteSelectionService Service for handling site selection
   * @param router Angular router for navigation
   */
  constructor(
    private authService: AuthService,
    private userContextService: UserContextService,
    private siteSelectionService: SiteSelectionService,
    private router: Router
  ) {}

  /**
   * Lifecycle hook that initializes component data and subscriptions
   */
  ngOnInit(): void {
    // Subscribe to user context changes
    this.subscriptions.add(
      this.userContextService.currentUser$.subscribe(user => {
        this.currentUser = user;
        this.updatePermissions();
      })
    );

    // Subscribe to site context changes
    this.subscriptions.add(
      this.userContextService.currentSite$.subscribe(site => {
        this.currentSite = site;
        this.updatePermissions();
      })
    );

    // Subscribe to authentication state changes
    this.subscriptions.add(
      this.authService.isAuthenticated().subscribe(isAuthenticated => {
        this.isAuthenticated = isAuthenticated;
        this.updatePermissions();
      })
    );

    // Check if on mobile view
    this.isMobile = window.innerWidth < 768;
    
    // Add resize event listener for responsive design
    window.addEventListener('resize', this.onResize.bind(this));
  }

  /**
   * Lifecycle hook that cleans up subscriptions
   */
  ngOnDestroy(): void {
    // Clean up subscriptions
    this.subscriptions.unsubscribe();
    
    // Remove resize event listener
    window.removeEventListener('resize', this.onResize.bind(this));
  }

  /**
   * Toggles the expanded state of the navigation menu
   */
  toggleMenu(): void {
    this.isExpanded = !this.isExpanded;
  }

  /**
   * Closes the navigation menu
   */
  closeMenu(): void {
    this.isExpanded = false;
  }

  /**
   * Handles user logout
   */
  logout(): void {
    this.authService.logout().pipe(
      take(1) // Ensure we only subscribe once
    ).subscribe(() => {
      this.closeMenu();
    });
  }

  /**
   * Initiates the site selection process
   */
  changeSite(): void {
    // Get current path to redirect back after site selection
    const currentPath = this.router.url;
    this.siteSelectionService.startSiteSelection(currentPath);
    this.closeMenu();
  }

  /**
   * Updates permission flags based on current user context
   */
  updatePermissions(): void {
    // Check if user is admin for current site
    this.isAdmin = this.userContextService.isAdmin();
    
    // Check if user is editor for current site
    this.isEditor = this.userContextService.isEditor();
    
    // Check if user has access to any sites
    this.hasSiteAccess = this.currentUser?.sites?.length > 0 || false;
    
    // Check if user has access to multiple sites
    this.hasMultipleSites = this.currentUser?.sites?.length > 1 || false;
  }

  /**
   * Checks if a specific route is currently active
   * 
   * @param route Route path to check
   * @returns True if route is active
   */
  isActive(route: string): boolean {
    // Check if current URL matches or starts with the given route
    return this.router.url === route || this.router.url.startsWith(`${route}/`);
  }

  /**
   * Handles window resize events to update mobile view state
   */
  onResize(): void {
    const wasChange = this.isMobile !== (window.innerWidth < 768);
    this.isMobile = window.innerWidth < 768;
    
    // If switching to mobile view, ensure menu is closed
    if (wasChange && this.isMobile) {
      this.isExpanded = false;
    }
  }
}