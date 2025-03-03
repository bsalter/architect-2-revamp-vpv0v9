import { Component, OnInit, OnDestroy } from '@angular/core'; // @angular/core v16.2.0
import { Router } from '@angular/router'; // @angular/router v16.2.0
import { Observable, Subject } from 'rxjs'; // rxjs v7.8.1
import { takeUntil } from 'rxjs/operators'; // rxjs/operators v7.8.1

import { AuthService } from '../../../core/auth/auth.service';
import { UserContextService } from '../../../core/auth/user-context.service';
import { SiteSelectionService } from '../../../core/auth/site-selection.service';
import { User } from '../../../core/auth/user.model';
import { SiteService } from '../../../features/sites/services/site.service';
import { SiteWithRole } from '../../../features/sites/models/site.model';

/**
 * Component responsible for rendering the application header with authentication status, 
 * user info, site selector, and navigation elements
 */
@Component({
  selector: 'app-header',
  templateUrl: './header.component.html',
  styleUrls: ['./header.component.scss']
})
export class HeaderComponent implements OnInit, OnDestroy {
  currentUser: User | null = null;
  currentSiteId: number | null = null;
  currentSiteName: string = '';
  availableSites: SiteWithRole[] = [];
  isDropdownOpen: boolean = false;
  isMobile: boolean = false;
  isLoading: boolean = false;
  isUserMenuOpen: boolean = false;
  private destroy$ = new Subject<void>();

  /**
   * Initializes the header component with required services
   */
  constructor(
    private authService: AuthService,
    private userContextService: UserContextService,
    private siteSelectionService: SiteSelectionService,
    private siteService: SiteService,
    private router: Router
  ) {}

  /**
   * Lifecycle hook that initializes component and subscribes to authentication and site context
   */
  ngOnInit(): void {
    // Subscribe to user context changes
    this.userContextService.currentUser$
      .pipe(takeUntil(this.destroy$))
      .subscribe(user => {
        this.currentUser = user;
        if (user) {
          this.loadAvailableSites();
        } else {
          // Clear sites when user is not authenticated
          this.availableSites = [];
        }
      });

    // Subscribe to site context changes
    this.userContextService.currentSiteId$
      .pipe(takeUntil(this.destroy$))
      .subscribe(siteId => {
        this.currentSiteId = siteId;
      });

    // Subscribe to current site name
    this.siteService.getCurrentSiteName()
      .pipe(takeUntil(this.destroy$))
      .subscribe(name => {
        this.currentSiteName = name || 'No site selected';
      });

    // Check screen size and set up resize listener for responsive design
    this.checkScreenSize();
    window.addEventListener('resize', this.checkScreenSize.bind(this));
  }

  /**
   * Lifecycle hook that cleans up subscriptions when component is destroyed
   */
  ngOnDestroy(): void {
    // Clean up subscriptions and event listeners
    this.destroy$.next();
    this.destroy$.complete();
    window.removeEventListener('resize', this.checkScreenSize.bind(this));
  }

  /**
   * Loads the list of sites available to the current user
   */
  loadAvailableSites(): void {
    this.isLoading = true;
    this.siteService.getUserSites(true)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (sites) => {
          this.availableSites = sites;
          this.isLoading = false;
        },
        error: (error) => {
          console.error('Error loading sites:', error);
          this.isLoading = false;
        }
      });
  }

  /**
   * Toggles the site selection dropdown visibility
   */
  toggleSiteDropdown(): void {
    // Don't open dropdown if user has no sites or only one site
    if (!this.currentUser || this.availableSites.length <= 1) {
      return;
    }
    
    this.isDropdownOpen = !this.isDropdownOpen;
    // Close user menu if opening site dropdown
    if (this.isDropdownOpen) {
      this.isUserMenuOpen = false;
    }
  }

  /**
   * Toggles the user menu dropdown visibility
   */
  toggleUserMenu(): void {
    this.isUserMenuOpen = !this.isUserMenuOpen;
    // Close site dropdown if opening user menu
    if (this.isUserMenuOpen) {
      this.isDropdownOpen = false;
    }
  }

  /**
   * Handles site selection from the dropdown
   * 
   * @param siteId - The ID of the selected site
   */
  selectSite(siteId: number): void {
    // Don't do anything if it's the same site
    if (siteId === this.currentSiteId) {
      this.isDropdownOpen = false;
      return;
    }

    // Check if user has access to this site
    if (!this.currentUser || !this.currentUser.hasSiteAccess(siteId)) {
      console.error('User does not have access to this site');
      this.isDropdownOpen = false;
      return;
    }

    // Set the current site ID
    const success = this.userContextService.setCurrentSiteId(siteId);
    if (!success) {
      console.error('Failed to set current site');
      this.isDropdownOpen = false;
      return;
    }
    
    // Close dropdown
    this.isDropdownOpen = false;
    
    // Navigate to dashboard after site change
    this.router.navigate(['/dashboard']);
  }

  /**
   * Handles user logout action
   */
  logout(): void {
    this.authService.logout().subscribe({
      next: () => {
        // Close any open menus
        this.isDropdownOpen = false;
        this.isUserMenuOpen = false;
        
        // Navigate to login page
        this.router.navigate(['/login']);
      },
      error: (error) => {
        console.error('Logout error:', error);
      }
    });
  }

  /**
   * Navigates to the user profile page
   */
  navigateToProfile(): void {
    this.isUserMenuOpen = false;
    
    // Navigate to user profile page
    // For MVP, this might redirect to dashboard with a notification
    // that profile management is coming soon
    this.router.navigate(['/profile']);
  }

  /**
   * Checks if a user is currently authenticated
   * 
   * @returns True if user is authenticated, false otherwise
   */
  isAuthenticated(): boolean {
    return !!this.currentUser;
  }

  /**
   * Handles clicks outside dropdown menus to close them
   */
  onClickOutside(): void {
    if (this.isDropdownOpen) {
      this.isDropdownOpen = false;
    }
    if (this.isUserMenuOpen) {
      this.isUserMenuOpen = false;
    }
  }

  /**
   * Checks screen size and updates isMobile state
   */
  checkScreenSize(): void {
    this.isMobile = window.innerWidth < 768; // 768px is the medium breakpoint (MD)
  }
}