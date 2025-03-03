import { Component, OnInit, OnDestroy, EventEmitter, Output } from '@angular/core'; // @angular/core 16.2.0
import { Subject, Subscription } from 'rxjs'; // rxjs 7.8.1
import { takeUntil, finalize } from 'rxjs/operators'; // rxjs/operators 7.8.1

import { SiteWithRole } from '../../../../features/sites/models/site.model';
import { SiteSelectionService } from '../../../../core/auth/site-selection.service';
import { UserContextService } from '../../../../core/auth/user-context.service';

/**
 * Component that implements the site selection interface displayed after successful authentication
 * when a user has access to multiple sites. It allows the user to choose which site to access
 * before proceeding to the application.
 */
@Component({
  selector: 'app-site-selection',
  templateUrl: './site-selection.component.html',
  styleUrls: ['./site-selection.component.scss']
})
export class SiteSelectionComponent implements OnInit, OnDestroy {
  /** List of sites the user has access to */
  availableSites: SiteWithRole[] = [];
  
  /** Currently selected site ID */
  selectedSiteId: number | null = null;
  
  /** Indicates if a data operation is in progress */
  isLoading: boolean = false;
  
  /** Indicates if an error has occurred */
  hasError: boolean = false;
  
  /** Error message to display to the user */
  errorMessage: string = '';
  
  /** Event emitted when a site is successfully selected */
  @Output() siteSelected = new EventEmitter<void>();
  
  /** Event emitted when the site selection is cancelled */
  @Output() cancel = new EventEmitter<void>();
  
  /** Subject used to clean up subscriptions when component is destroyed */
  private destroy$ = new Subject<void>();
  
  /** Collection of subscriptions to clean up on component destruction */
  private subscriptions = new Subscription();

  /**
   * Creates an instance of SiteSelectionComponent.
   * 
   * @param siteSelectionService Service for managing the site selection process
   * @param userContextService Service for accessing user information
   */
  constructor(
    private siteSelectionService: SiteSelectionService,
    private userContextService: UserContextService
  ) {}

  /**
   * Lifecycle hook that initializes the component and loads available sites.
   */
  ngOnInit(): void {
    // Subscribe to loading state from the site selection service
    this.subscriptions.add(
      this.siteSelectionService.isLoading$
        .pipe(takeUntil(this.destroy$))
        .subscribe(isLoading => {
          this.isLoading = isLoading;
        })
    );
    
    // Load the list of available sites
    this.loadAvailableSites();
    
    // Verify the user is authenticated
    const currentUser = this.userContextService.getCurrentUser();
    if (!currentUser) {
      this.hasError = true;
      this.errorMessage = 'User not authenticated. Please log in again.';
    }
  }

  /**
   * Lifecycle hook for cleanup when component is destroyed.
   */
  ngOnDestroy(): void {
    // Signal completion to all observables
    this.destroy$.next();
    this.destroy$.complete();
    
    // Unsubscribe from all subscriptions
    this.subscriptions.unsubscribe();
  }

  /**
   * Loads the list of sites available to the current user.
   */
  loadAvailableSites(): void {
    // Reset error state
    this.hasError = false;
    this.errorMessage = '';
    
    // Get available sites from the service
    this.siteSelectionService.getAvailableSites()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (sites) => {
          this.availableSites = sites;
          
          // If sites are available, select the first one by default
          if (sites.length > 0) {
            this.selectedSiteId = sites[0].id;
          }
        },
        error: (error) => {
          // Handle error loading sites
          this.hasError = true;
          if (error.status === 401) {
            this.errorMessage = 'Your session has expired. Please log in again.';
          } else if (error.status === 403) {
            this.errorMessage = 'You do not have permission to access site information.';
          } else {
            this.errorMessage = 'Failed to load available sites. Please try again.';
          }
          console.error('Error loading sites:', error);
        }
      });
  }

  /**
   * Updates the selected site ID when a user selects a site.
   * 
   * @param siteId The ID of the selected site
   */
  updateSelectedSite(siteId: number): void {
    this.selectedSiteId = siteId;
    // Reset any error messages when user selects a site
    this.hasError = false;
    this.errorMessage = '';
  }

  /**
   * Handles the site selection confirmation and triggers navigation.
   */
  selectSite(): void {
    // Validate a site has been selected
    if (this.selectedSiteId === null) {
      this.hasError = true;
      this.errorMessage = 'Please select a site before continuing.';
      return;
    }
    
    // Reset error state
    this.hasError = false;
    this.errorMessage = '';
    
    // Call service to select the site
    this.siteSelectionService.selectSite(this.selectedSiteId)
      .pipe(
        finalize(() => {
          // Any final actions after process completes (success or failure)
        })
      )
      .subscribe({
        next: () => {
          // Emit event to notify parent component of successful selection
          this.siteSelected.emit();
        },
        error: (error) => {
          // Handle site selection error
          this.hasError = true;
          if (error.message && error.message.includes('No access to selected site')) {
            this.errorMessage = 'You do not have access to the selected site. Please choose another site.';
          } else if (error.message && error.message.includes('Failed to set current site')) {
            this.errorMessage = 'Could not set the selected site as your current site. Please try again.';
          } else {
            this.errorMessage = 'Failed to select site. Please try again.';
          }
          console.error('Error selecting site:', error);
        }
      });
  }

  /**
   * Handles the cancellation of site selection.
   */
  cancelSelection(): void {
    // Call service to cancel site selection
    this.siteSelectionService.cancelSiteSelection();
    
    // Emit event to notify parent component
    this.cancel.emit();
  }

  /**
   * Gets a formatted display string for a site role.
   * 
   * @param role The role string to format
   * @returns Formatted role display string
   */
  getSiteRoleDisplay(role: string): string {
    if (!role) return '';
    
    // Convert camel case or snake case to title case with spaces
    return role
      .replace(/([A-Z])/g, ' $1') // Insert space before capital letters
      .replace(/_/g, ' ')         // Replace underscores with spaces
      .replace(/^\w/, c => c.toUpperCase()) // Capitalize first letter
      .trim();                    // Remove any extra spaces
  }
}