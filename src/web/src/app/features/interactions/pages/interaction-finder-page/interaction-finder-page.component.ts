import { Component, OnInit, OnDestroy, ViewChild } from '@angular/core'; // @angular/core v16.2.0
import { Router } from '@angular/router'; // @angular/router v16.2.0
import { Subject, Observable, Subscription, combineLatest } from 'rxjs'; // rxjs v7.8.1
import { takeUntil, debounceTime, distinctUntilChanged, filter } from 'rxjs/operators'; // rxjs/operators v7.8.1

import { Interaction, InteractionType } from '../../models/interaction.model';
import { SearchResults, SearchResultItem } from '../../models/search-results.model';
import { SearchQuery, Filter } from '../../models/filter.model';
import { SearchService } from '../../services/search.service';
import { InteractionService } from '../../services/interaction.service';
import { FinderTableComponent } from '../../components/finder-table/finder-table.component';
import { FinderFiltersComponent } from '../../components/finder-filters/finder-filters.component';
import { UserContextService } from '../../../../core/auth/user-context.service';
import { ToastService } from '../../../../shared/services/toast.service';

// Constants for pagination and search debounce
const DEFAULT_PAGE_SIZE = 10;
const SEARCH_DEBOUNCE_TIME = 300;

/**
 * Main container component for the Interaction Finder interface, coordinating search, 
 * filtering, and table functionality with site-scoped access control.
 */
@Component({
  selector: 'app-interaction-finder-page',
  templateUrl: './interaction-finder-page.component.html',
  styleUrls: ['./interaction-finder-page.component.scss']
})
export class InteractionFinderPageComponent implements OnInit, OnDestroy {
  @ViewChild('finderTable') finderTable: FinderTableComponent;
  @ViewChild('finderFilters') finderFilters: FinderFiltersComponent;

  // Data and state properties
  searchResults: SearchResults;
  currentQuery: SearchQuery;
  searchTerm = '';
  activeFilters: Filter[] = [];
  isLoading = false;
  hasError = false;
  errorMessage = '';
  canCreateInteraction = false;
  showAdvancedFilters = false;

  // Subscription management
  destroy$ = new Subject<void>();
  searchSubscription: Subscription;
  loadingSubscription: Subscription;
  errorSubscription: Subscription;
  siteChangeSubscription: Subscription;

  /**
   * Initializes the component with required dependencies
   */
  constructor(
    private searchService: SearchService,
    private interactionService: InteractionService,
    private userContextService: UserContextService,
    private router: Router,
    private toastService: ToastService
  ) {
    // Initialize searchResults with empty state
    this.searchResults = {
      items: [],
      metadata: {
        total: 0,
        page: 1,
        pageSize: DEFAULT_PAGE_SIZE,
        pages: 0,
        executionTimeMs: 0
      },
      query: {
        page: 1,
        pageSize: DEFAULT_PAGE_SIZE
      },
      loading: false
    };

    // Initialize currentQuery with default values
    this.currentQuery = {
      page: 1,
      pageSize: DEFAULT_PAGE_SIZE
    };
  }

  /**
   * Lifecycle hook that initializes the component
   */
  ngOnInit(): void {
    // Check user permissions to determine if they can create interactions
    this.canCreateInteraction = this.userContextService.isEditor();

    // Subscribe to search results
    this.searchSubscription = this.searchService.searchResults$
      .pipe(takeUntil(this.destroy$))
      .subscribe(results => {
        this.searchResults = results;
      });

    // Subscribe to loading state
    this.loadingSubscription = this.searchService.loading$
      .pipe(takeUntil(this.destroy$))
      .subscribe(loading => {
        this.isLoading = loading;
      });

    // Subscribe to error state
    this.errorSubscription = this.searchService.error$
      .pipe(takeUntil(this.destroy$))
      .subscribe(error => {
        if (error) {
          this.hasError = true;
          this.errorMessage = error;
        } else {
          this.hasError = false;
          this.errorMessage = '';
        }
      });

    // Subscribe to site changes to reset search when site context changes
    this.siteChangeSubscription = this.userContextService.currentSiteId$
      .pipe(
        takeUntil(this.destroy$),
        filter(siteId => !!siteId) // Only process valid site IDs
      )
      .subscribe(() => {
        this.handleSiteChange();
      });

    // Initialize search with default parameters
    this.performSearch(true);
  }

  /**
   * Lifecycle hook that cleans up subscriptions
   */
  ngOnDestroy(): void {
    // Complete all subscriptions
    this.destroy$.next();
    this.destroy$.complete();

    // Explicitly unsubscribe from any direct subscriptions
    if (this.searchSubscription) {
      this.searchSubscription.unsubscribe();
    }
    if (this.loadingSubscription) {
      this.loadingSubscription.unsubscribe();
    }
    if (this.errorSubscription) {
      this.errorSubscription.unsubscribe();
    }
    if (this.siteChangeSubscription) {
      this.siteChangeSubscription.unsubscribe();
    }
  }

  /**
   * Executes a search based on current search parameters
   * 
   * @param resetPagination Whether to reset to first page
   */
  performSearch(resetPagination: boolean = true): void {
    // Create new SearchQuery object with current parameters
    const query: SearchQuery = {
      globalSearch: this.searchTerm,
      filters: this.activeFilters,
      page: resetPagination ? 1 : this.currentQuery.page,
      pageSize: DEFAULT_PAGE_SIZE
    };

    // Add sort if available
    if (this.currentQuery.sortField) {
      query.sortField = this.currentQuery.sortField;
      query.sortDirection = this.currentQuery.sortDirection;
    }

    // Execute the search and update current query
    this.searchService.advancedSearch(query);
    this.currentQuery = query;
  }

  /**
   * Handles changes to the search input field
   * 
   * @param term The search text entered by the user
   */
  onSearchInput(term: string): void {
    this.searchTerm = term;
    // Debounce is handled by the template using a timer
    this.performSearch(true);
  }

  /**
   * Handles changes to the filter selection
   * 
   * @param filters Array of active filters
   */
  onFiltersChanged(filters: Filter[]): void {
    this.activeFilters = filters;
    this.performSearch(true);
  }

  /**
   * Handles changes to table sorting
   * 
   * @param sortEvent Sort field and direction
   */
  onSortChanged(sortEvent: any): void {
    this.currentQuery.sortField = sortEvent.sortField;
    this.currentQuery.sortDirection = sortEvent.sortDirection;
    this.performSearch(false); // Don't reset pagination when sorting
  }

  /**
   * Toggles the advanced filter panel visibility
   */
  onFilterToggle(): void {
    this.showAdvancedFilters = !this.showAdvancedFilters;
    if (this.finderFilters) {
      this.finderFilters.toggleFilterPanel();
    }
  }

  /**
   * Handles the filter panel being closed
   */
  onFilterPanelClosed(): void {
    this.showAdvancedFilters = false;
  }

  /**
   * Handles pagination events
   * 
   * @param page The page number to navigate to
   */
  onPageChanged(page: number): void {
    this.currentQuery.page = page;
    this.performSearch(false); // Don't reset pagination
  }

  /**
   * Navigates to the interaction creation page
   */
  onCreateInteraction(): void {
    this.router.navigate(['/interactions/create']);
  }

  /**
   * Handles viewing an interaction's details
   * 
   * @param id Interaction ID to view
   */
  onViewInteraction(id: number): void {
    this.router.navigate(['/interactions', id]);
  }

  /**
   * Handles editing an interaction
   * 
   * @param id Interaction ID to edit
   */
  onEditInteraction(id: number): void {
    this.router.navigate(['/interactions', id, 'edit']);
  }

  /**
   * Handles deleting an interaction
   * 
   * @param interaction The interaction to delete
   */
  onDeleteInteraction(interaction: Interaction): void {
    this.interactionService.deleteInteraction(interaction.id)
      .subscribe({
        next: () => {
          this.toastService.showSuccess('Interaction deleted successfully');
          // Refresh search results
          this.performSearch(false);
        },
        error: (error) => {
          this.toastService.showError('Failed to delete interaction: ' + error.message);
        }
      });
  }

  /**
   * Handles changes to the user's active site
   */
  handleSiteChange(): void {
    // Reset search parameters
    this.searchTerm = '';
    this.activeFilters = [];
    this.currentQuery = {
      page: 1,
      pageSize: DEFAULT_PAGE_SIZE
    };

    // Perform search with new site context
    this.performSearch(true);
  }

  /**
   * Clears all search parameters and filters
   */
  clearSearch(): void {
    this.searchTerm = '';
    this.activeFilters = [];
    if (this.finderFilters) {
      this.finderFilters.clearFilters();
    }
    this.performSearch(true);
  }

  /**
   * Gets the count of currently active filters
   * 
   * @returns Count of active filters
   */
  getActiveFilterCount(): number {
    return this.activeFilters?.length || 0;
  }
}