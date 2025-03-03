import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { ReactiveFormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';
import { BehaviorSubject, of } from 'rxjs';
import { NO_ERRORS_SCHEMA } from '@angular/core';

import { InteractionFinderPageComponent } from './interaction-finder-page.component';
import { SearchService } from '../../services/search.service';
import { FinderTableComponent } from '../../components/finder-table/finder-table.component';
import { FinderFiltersComponent } from '../../components/finder-filters/finder-filters.component';
import { SearchResults } from '../../models/search-results.model';
import { Filter } from '../../models/filter.model';
import { SiteSelectionService } from '../../../../core/auth/site-selection.service';
import { BreadcrumbService } from '../../../../shared/services/breadcrumb.service';
import { ToastService } from '../../../../shared/services/toast.service';
import { InteractionService } from '../../services/interaction.service';
import { UserContextService } from '../../../../core/auth/user-context.service';

describe('InteractionFinderPageComponent', () => {
  let component: InteractionFinderPageComponent;
  let fixture: ComponentFixture<InteractionFinderPageComponent>;
  
  // Mock services
  let searchServiceMock: jasmine.SpyObj<SearchService>;
  let interactionServiceMock: jasmine.SpyObj<InteractionService>;
  let siteSelectionServiceMock: jasmine.SpyObj<SiteSelectionService>;
  let userContextServiceMock: jasmine.SpyObj<UserContextService>;
  let breadcrumbServiceMock: jasmine.SpyObj<BreadcrumbService>;
  let toastServiceMock: jasmine.SpyObj<ToastService>;
  let routerMock: jasmine.SpyObj<Router>;
  
  // Mock observables
  let searchResults$: BehaviorSubject<SearchResults>;
  let loading$: BehaviorSubject<boolean>;
  let error$: BehaviorSubject<string>;
  
  // Mock data
  const mockSearchResults: SearchResults = {
    items: [
      {
        id: 1,
        title: 'Test Interaction',
        type: 'Meeting',
        lead: 'John Doe',
        startDatetime: new Date(),
        endDatetime: new Date(),
        timezone: 'UTC',
        location: 'Test Location',
        siteId: 1,
        siteName: 'Test Site'
      }
    ],
    metadata: {
      total: 1,
      page: 1,
      pageSize: 10,
      pages: 1,
      executionTimeMs: 100
    },
    query: {
      page: 1,
      pageSize: 10
    },
    loading: false
  };

  // Helper function to create the component with all dependencies properly configured
  function createComponent() {
    // Create mock services
    searchResults$ = new BehaviorSubject<SearchResults>(mockSearchResults);
    loading$ = new BehaviorSubject<boolean>(false);
    error$ = new BehaviorSubject<string>('');
    
    searchServiceMock = jasmine.createSpyObj('SearchService', [
      'globalSearch',
      'advancedSearch',
      'refreshSearch'
    ], {
      searchResults$: searchResults$.asObservable(),
      loading$: loading$.asObservable(),
      error$: error$.asObservable()
    });
    
    interactionServiceMock = jasmine.createSpyObj('InteractionService', [
      'deleteInteraction'
    ]);
    
    siteSelectionServiceMock = jasmine.createSpyObj('SiteSelectionService', [
      'getCurrentSiteId'
    ]);
    
    userContextServiceMock = jasmine.createSpyObj('UserContextService', [
      'isEditor'
    ], {
      currentSiteId$: new BehaviorSubject<number>(1).asObservable()
    });
    userContextServiceMock.isEditor.and.returnValue(true);
    
    breadcrumbServiceMock = jasmine.createSpyObj('BreadcrumbService', [
      'setBreadcrumbs'
    ]);
    
    toastServiceMock = jasmine.createSpyObj('ToastService', [
      'showSuccess',
      'showError'
    ]);
    
    routerMock = jasmine.createSpyObj('Router', ['navigate']);
    
    TestBed.configureTestingModule({
      imports: [
        ReactiveFormsModule,
        RouterTestingModule
      ],
      declarations: [
        InteractionFinderPageComponent
      ],
      providers: [
        { provide: SearchService, useValue: searchServiceMock },
        { provide: InteractionService, useValue: interactionServiceMock },
        { provide: SiteSelectionService, useValue: siteSelectionServiceMock },
        { provide: UserContextService, useValue: userContextServiceMock },
        { provide: BreadcrumbService, useValue: breadcrumbServiceMock },
        { provide: ToastService, useValue: toastServiceMock },
        { provide: Router, useValue: routerMock }
      ],
      schemas: [NO_ERRORS_SCHEMA] // Ignore unknown elements and properties
    }).compileComponents();
    
    fixture = TestBed.createComponent(InteractionFinderPageComponent);
    component = fixture.componentInstance;
    
    // Set default site ID
    siteSelectionServiceMock.getCurrentSiteId.and.returnValue(1);
    
    fixture.detectChanges();
  }
  
  // Test component initialization
  it('should create the component', () => {
    createComponent();
    expect(component).toBeTruthy();
  });

  it('should initialize with default search parameters', () => {
    createComponent();
    expect(component.searchTerm).toBe('');
    expect(component.activeFilters).toEqual([]);
    expect(component.searchResults).toBeTruthy();
    expect(searchServiceMock.advancedSearch).toHaveBeenCalled();
  });

  it('should subscribe to search results during initialization', () => {
    createComponent();
    expect(component.searchResults).toEqual(mockSearchResults);
  });
  
  it('should check user permissions for interaction creation', () => {
    // Default is set to true in our mock setup
    createComponent();
    expect(component.canCreateInteraction).toBeTrue();
    
    // Change to false and recreate component
    userContextServiceMock.isEditor.and.returnValue(false);
    fixture = TestBed.createComponent(InteractionFinderPageComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
    
    expect(component.canCreateInteraction).toBeFalse();
  });

  // Test search functionality
  it('should perform search when search input changes', () => {
    createComponent();
    const searchTerm = 'test search';
    
    component.onSearchInput(searchTerm);
    
    expect(component.searchTerm).toBe(searchTerm);
    expect(searchServiceMock.advancedSearch).toHaveBeenCalled();
    
    // Verify search parameters were correct
    const searchCall = searchServiceMock.advancedSearch.calls.mostRecent();
    expect(searchCall.args[0].globalSearch).toBe(searchTerm);
    expect(searchCall.args[0].page).toBe(1); // Should reset to page 1
  });

  // Test filter operations
  it('should update filters when filter change event is received', () => {
    createComponent();
    const mockFilters: Filter[] = [
      {
        field: 'type',
        operator: 'eq',
        value: 'Meeting'
      }
    ];
    
    component.onFiltersChanged(mockFilters);
    
    expect(component.activeFilters).toEqual(mockFilters);
    expect(searchServiceMock.advancedSearch).toHaveBeenCalled();
    
    // Verify search parameters were correct
    const searchCall = searchServiceMock.advancedSearch.calls.mostRecent();
    expect(searchCall.args[0].filters).toEqual(mockFilters);
    expect(searchCall.args[0].page).toBe(1); // Should reset to page 1
  });

  // Test pagination
  it('should change page without resetting filters', () => {
    createComponent();
    const newPage = 2;
    
    component.onPageChanged(newPage);
    
    expect(component.currentQuery.page).toBe(newPage);
    expect(searchServiceMock.advancedSearch).toHaveBeenCalled();
    
    // Verify search parameters were correct
    const searchCall = searchServiceMock.advancedSearch.calls.mostRecent();
    expect(searchCall.args[0].page).toBe(newPage);
  });

  // Test sorting
  it('should update sort criteria without resetting pagination', () => {
    createComponent();
    const sortEvent = {
      sortField: 'title',
      sortDirection: 'asc'
    };
    
    component.onSortChanged(sortEvent);
    
    expect(component.currentQuery.sortField).toBe(sortEvent.sortField);
    expect(component.currentQuery.sortDirection).toBe(sortEvent.sortDirection);
    expect(searchServiceMock.advancedSearch).toHaveBeenCalled();
    
    // Verify search parameters were correct
    const searchCall = searchServiceMock.advancedSearch.calls.mostRecent();
    expect(searchCall.args[0].sortField).toBe(sortEvent.sortField);
    expect(searchCall.args[0].sortDirection).toBe(sortEvent.sortDirection);
    expect(searchCall.args[0].page).not.toBe(1); // Should not reset page
  });

  // Test CRUD operations
  it('should navigate to interaction creation page', () => {
    createComponent();
    
    component.onCreateInteraction();
    
    expect(routerMock.navigate).toHaveBeenCalledWith(['/interactions/create']);
  });

  it('should navigate to interaction view page', () => {
    createComponent();
    const mockId = 123;
    
    component.onViewInteraction(mockId);
    
    expect(routerMock.navigate).toHaveBeenCalledWith(['/interactions', mockId]);
  });

  it('should navigate to interaction edit page', () => {
    createComponent();
    const mockId = 123;
    
    component.onEditInteraction(mockId);
    
    expect(routerMock.navigate).toHaveBeenCalledWith(['/interactions', mockId, 'edit']);
  });
  
  it('should delete an interaction and refresh search results', fakeAsync(() => {
    createComponent();
    
    const mockInteraction = {
      id: 123,
      title: 'Test Interaction',
      type: 'Meeting',
      lead: 'John Doe',
      startDatetime: new Date(),
      endDatetime: new Date(),
      timezone: 'UTC',
      location: 'Test Location',
      siteId: 1
    };
    
    interactionServiceMock.deleteInteraction.and.returnValue(of(true));
    
    component.onDeleteInteraction(mockInteraction);
    tick(); // Process the observable
    
    expect(interactionServiceMock.deleteInteraction).toHaveBeenCalledWith(mockInteraction.id);
    expect(toastServiceMock.showSuccess).toHaveBeenCalled();
    expect(searchServiceMock.advancedSearch).toHaveBeenCalled();
  }));

  it('should show error toast when delete fails', fakeAsync(() => {
    createComponent();
    
    const mockInteraction = {
      id: 123,
      title: 'Test Interaction',
      type: 'Meeting',
      lead: 'John Doe',
      startDatetime: new Date(),
      endDatetime: new Date(),
      timezone: 'UTC',
      location: 'Test Location',
      siteId: 1
    };
    
    const mockError = { message: 'Delete failed' };
    interactionServiceMock.deleteInteraction.and.returnValue(throwError(() => mockError));
    
    component.onDeleteInteraction(mockInteraction);
    tick(); // Process the observable
    
    expect(interactionServiceMock.deleteInteraction).toHaveBeenCalledWith(mockInteraction.id);
    expect(toastServiceMock.showError).toHaveBeenCalledWith(jasmine.stringMatching(/Failed to delete interaction/));
  }));

  // Test site change handling
  it('should reset search parameters and perform search when site changes', () => {
    createComponent();
    
    // Setup pre-existing search state
    component.searchTerm = 'existing search';
    component.activeFilters = [{ field: 'type', operator: 'eq', value: 'Call' }];
    component.currentQuery = {
      page: 2,
      pageSize: 10,
      sortField: 'title',
      sortDirection: 'asc'
    };
    
    component.handleSiteChange();
    
    // Verify parameters were reset
    expect(component.searchTerm).toBe('');
    expect(component.activeFilters).toEqual([]);
    expect(component.currentQuery.page).toBe(1);
    expect(component.currentQuery.sortField).toBeUndefined();
    expect(component.currentQuery.sortDirection).toBeUndefined();
    
    // Verify search was performed
    expect(searchServiceMock.advancedSearch).toHaveBeenCalled();
  });

  // Test filter panel toggle
  it('should toggle filter panel visibility', () => {
    createComponent();
    
    // Mock the finder filters component reference
    component.finderFilters = jasmine.createSpyObj('FinderFilters', ['toggleFilterPanel']);
    
    // Initial state
    expect(component.showAdvancedFilters).toBeFalse();
    
    // Toggle on
    component.onFilterToggle();
    expect(component.showAdvancedFilters).toBeTrue();
    expect(component.finderFilters.toggleFilterPanel).toHaveBeenCalled();
    
    // Toggle off
    component.onFilterToggle();
    expect(component.showAdvancedFilters).toBeFalse();
    expect(component.finderFilters.toggleFilterPanel).toHaveBeenCalledTimes(2);
  });

  // Test filter panel closed event
  it('should handle filter panel closed event', () => {
    createComponent();
    
    component.showAdvancedFilters = true;
    component.onFilterPanelClosed();
    
    expect(component.showAdvancedFilters).toBeFalse();
  });

  // Test clear search functionality
  it('should clear search parameters', () => {
    createComponent();
    
    // Setup pre-existing search state
    component.searchTerm = 'existing search';
    component.activeFilters = [{ field: 'type', operator: 'eq', value: 'Call' }];
    
    // Mock the finder filters component reference
    component.finderFilters = jasmine.createSpyObj('FinderFilters', ['clearFilters']);
    
    component.clearSearch();
    
    expect(component.searchTerm).toBe('');
    expect(component.activeFilters).toEqual([]);
    expect(component.finderFilters.clearFilters).toHaveBeenCalled();
    expect(searchServiceMock.advancedSearch).toHaveBeenCalled();
  });
  
  // Test error handling
  it('should handle error states', () => {
    createComponent();
    
    // Simulate an error
    error$.next('Test error message');
    fixture.detectChanges();
    
    expect(component.hasError).toBeTrue();
    expect(component.errorMessage).toBe('Test error message');
    
    // Clear the error
    error$.next('');
    fixture.detectChanges();
    
    expect(component.hasError).toBeFalse();
    expect(component.errorMessage).toBe('');
  });
  
  // Test loading state
  it('should track loading state', () => {
    createComponent();
    
    // Initial state (not loading)
    expect(component.isLoading).toBeFalse();
    
    // Set loading to true
    loading$.next(true);
    fixture.detectChanges();
    
    expect(component.isLoading).toBeTrue();
    
    // Set loading back to false
    loading$.next(false);
    fixture.detectChanges();
    
    expect(component.isLoading).toBeFalse();
  });
  
  // Test active filter count
  it('should return correct filter count', () => {
    createComponent();
    
    // No filters
    component.activeFilters = [];
    expect(component.getActiveFilterCount()).toBe(0);
    
    // With filters
    component.activeFilters = [
      { field: 'type', operator: 'eq', value: 'Meeting' },
      { field: 'lead', operator: 'contains', value: 'John' }
    ];
    expect(component.getActiveFilterCount()).toBe(2);
    
    // With undefined
    component.activeFilters = undefined;
    expect(component.getActiveFilterCount()).toBe(0);
  });

  // Test lifecycle management
  it('should properly unsubscribe on destroy', () => {
    createComponent();
    
    // Spy on destroy$ next and complete methods
    spyOn(component.destroy$, 'next');
    spyOn(component.destroy$, 'complete');
    
    component.ngOnDestroy();
    
    expect(component.destroy$.next).toHaveBeenCalled();
    expect(component.destroy$.complete).toHaveBeenCalled();
  });
});