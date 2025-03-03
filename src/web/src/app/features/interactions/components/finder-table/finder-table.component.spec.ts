import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { Router } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';
import { ChangeDetectorRef } from '@angular/core';
import { of, BehaviorSubject } from 'rxjs';
import { GridApi, GridReadyEvent, RowSelectedEvent, CellClickedEvent } from 'ag-grid-community';

import { FinderTableComponent } from './finder-table.component';
import { InteractionService } from '../../services/interaction.service';
import { SearchService } from '../../services/search.service';
import { SiteSelectionService } from '../../../../core/auth/site-selection.service';
import { Interaction, InteractionType } from '../../models/interaction.model';
import { SearchResults } from '../../models/search-results.model';
import { Filter } from '../../models/filter.model';

describe('FinderTableComponent', () => {
  let component: FinderTableComponent;
  let fixture: ComponentFixture<FinderTableComponent>;

  // Mock data for testing
  const mockInteractions: Interaction[] = [
    {
      id: 1,
      siteId: 1,
      title: 'Team Kickoff Meeting',
      type: InteractionType.MEETING,
      lead: 'J. Smith',
      startDatetime: new Date('2023-06-12T10:00:00Z'),
      endDatetime: new Date('2023-06-12T11:00:00Z'),
      timezone: 'America/New_York',
      location: 'Conference Room A',
      description: 'Initial project kickoff meeting',
      notes: 'Prepare slides',
      createdBy: 1,
      createdAt: new Date('2023-06-05T10:00:00Z'),
      updatedAt: new Date('2023-06-05T10:00:00Z')
    },
    {
      id: 2,
      siteId: 1,
      title: 'Client Review Call',
      type: InteractionType.CALL,
      lead: 'M. Jones',
      startDatetime: new Date('2023-06-14T14:30:00Z'),
      endDatetime: new Date('2023-06-14T15:30:00Z'),
      timezone: 'America/New_York',
      location: 'Virtual',
      description: 'Review project progress with client',
      notes: '',
      createdBy: 1,
      createdAt: new Date('2023-06-10T09:00:00Z'),
      updatedAt: new Date('2023-06-10T09:00:00Z')
    }
  ];

  const mockSearchResults: SearchResults = {
    items: mockInteractions.map(interaction => ({
      id: interaction.id,
      title: interaction.title,
      type: interaction.type,
      lead: interaction.lead,
      startDatetime: interaction.startDatetime,
      endDatetime: interaction.endDatetime,
      timezone: interaction.timezone,
      location: interaction.location,
      siteId: interaction.siteId,
      siteName: 'Test Site'
    })),
    metadata: {
      total: 2,
      page: 1,
      pageSize: 10,
      pages: 1,
      executionTimeMs: 42
    },
    query: {
      page: 1,
      pageSize: 10
    },
    loading: false
  };

  /**
   * Helper function to create the component fixture
   */
  function createComponent(): void {
    fixture = TestBed.createComponent(FinderTableComponent);
    component = fixture.componentInstance;
    component.searchResults = mockSearchResults;
    fixture.detectChanges();
  }

  /**
   * Creates a mock InteractionService for testing
   * 
   * @param mockInteractions Sample interactions to return from the service
   * @returns A jasmine spy object for InteractionService
   */
  function mockInteractionService(mockInteractions: Interaction[]): object {
    const interactionService = jasmine.createSpyObj('InteractionService', [
      'getInteractions', 'deleteInteraction'
    ]);
    
    interactionService.getInteractions.and.returnValue(of({
      interactions: mockInteractions,
      total: mockInteractions.length,
      page: 1,
      pageSize: 10,
      pages: 1
    }));
    
    interactionService.deleteInteraction.and.returnValue(of(true));
    
    return interactionService;
  }

  /**
   * Creates a mock SearchService for testing
   * 
   * @param mockResults Sample search results to return from the service
   * @returns A jasmine spy object for SearchService
   */
  function mockSearchService(mockResults: SearchResults): object {
    const searchService = jasmine.createSpyObj('SearchService', [
      'search', 'globalSearch'
    ]);
    
    // Create a BehaviorSubject for searchResults$
    const searchResultsSubject = new BehaviorSubject<SearchResults>(mockResults);
    searchService.searchResults$ = searchResultsSubject;
    
    searchService.search.and.returnValue(of(mockResults));
    searchService.globalSearch.and.returnValue(of(mockResults));
    
    return searchService;
  }

  /**
   * Creates a mock SiteSelectionService for testing
   * 
   * @param siteId Site ID to return from getCurrentSiteId
   * @returns A jasmine spy object for SiteSelectionService
   */
  function mockSiteSelectionService(siteId: number = 1): object {
    const siteService = jasmine.createSpyObj('SiteSelectionService', [
      'getCurrentSiteId'
    ]);
    
    siteService.getCurrentSiteId.and.returnValue(siteId);
    
    return siteService;
  }

  /**
   * Creates a mock GridReadyEvent for testing grid initialization
   * 
   * @returns A mock grid ready event
   */
  function createMockGridReadyEvent(): GridReadyEvent {
    const mockGridApi = jasmine.createSpyObj('GridApi', [
      'setRowData', 'sizeColumnsToFit', 'getSortModel', 'getFilterModel'
    ]);
    
    return {
      api: mockGridApi,
      columnApi: null,
      type: 'gridReady'
    } as GridReadyEvent;
  }

  /**
   * Creates a mock RowSelectedEvent for testing row selection
   * 
   * @param selected Whether the row is selected
   * @param data The row data
   * @returns A mock row selected event
   */
  function createMockRowSelectedEvent(selected: boolean, data: object): RowSelectedEvent {
    return {
      type: 'rowSelected',
      node: {
        isSelected: () => selected,
        data
      },
      api: null,
      rowIndex: 0,
      source: null
    } as unknown as RowSelectedEvent;
  }

  /**
   * Creates a mock CellClickedEvent for testing cell click handling
   * 
   * @param colId The column ID that was clicked
   * @param data The row data
   * @returns A mock cell clicked event
   */
  function createMockCellClickedEvent(colId: string, data: object): CellClickedEvent {
    return {
      type: 'cellClicked',
      column: {
        getColId: () => colId
      },
      node: {
        setSelected: jasmine.createSpy('setSelected')
      },
      data,
      value: null,
      event: null,
      api: null,
      colDef: null,
      rowIndex: 0
    } as unknown as CellClickedEvent;
  }

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [FinderTableComponent],
      imports: [RouterTestingModule],
      providers: [
        { provide: InteractionService, useValue: mockInteractionService(mockInteractions) },
        { provide: SearchService, useValue: mockSearchService(mockSearchResults) },
        { provide: SiteSelectionService, useValue: mockSiteSelectionService() },
        ChangeDetectorRef
      ]
    }).compileComponents();
  }));

  beforeEach(() => {
    createComponent();
  });

  it('should create the component', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize column definitions', () => {
    expect(component.columnDefs).toBeDefined();
    expect(component.columnDefs.length).toBeGreaterThan(0);
    // Verify essential columns are defined
    const columnFields = component.columnDefs.map(col => col.field);
    expect(columnFields).toContain('title');
    expect(columnFields).toContain('type');
    expect(columnFields).toContain('lead');
    expect(columnFields).toContain('startDatetime');
    expect(columnFields).toContain('location');
  });

  it('should initialize grid options with correct settings', () => {
    expect(component.gridOptions).toBeDefined();
    expect(component.gridOptions.rowSelection).toBe('single');
    expect(component.gridOptions.pagination).toBe(true);
  });

  it('should handle grid ready event', () => {
    const mockEvent = createMockGridReadyEvent();
    component.onGridReady(mockEvent);
    
    expect(component.gridApi).toBe(mockEvent.api);
    expect(mockEvent.api.setRowData).toHaveBeenCalledWith(mockSearchResults.items);
  });

  it('should subscribe to search results on init', () => {
    // Re-create component to test ngOnInit
    fixture = TestBed.createComponent(FinderTableComponent);
    component = fixture.componentInstance;
    
    // Mock grid API before initialization
    component.gridApi = jasmine.createSpyObj('GridApi', ['setRowData']);
    
    // Call ngOnInit
    component.ngOnInit();
    
    // Verify subscribe is working
    const searchService = TestBed.inject(SearchService);
    
    // Update search results
    const newResults = { ...mockSearchResults, items: [mockSearchResults.items[0]] };
    (searchService.searchResults$ as BehaviorSubject<SearchResults>).next(newResults);
    
    // Verify grid data was updated
    expect(component.gridApi.setRowData).toHaveBeenCalledWith(newResults.items);
  });

  it('should emit viewInteraction event when row is selected', () => {
    spyOn(component.viewInteraction, 'emit');
    
    const mockEvent = createMockRowSelectedEvent(true, mockSearchResults.items[0]);
    component.onRowSelected(mockEvent);
    
    expect(component.viewInteraction.emit).toHaveBeenCalledWith(mockSearchResults.items[0].id);
  });

  it('should prevent row selection when clicking in action column', () => {
    const mockEvent = createMockCellClickedEvent('id', mockSearchResults.items[0]);
    
    component.onCellClicked(mockEvent);
    
    expect(mockEvent.node.setSelected).toHaveBeenCalledWith(false);
  });

  it('should emit sortChanged event with sort parameters when sort changes', () => {
    spyOn(component.sortChanged, 'emit');
    
    // Setup grid API with sort model
    component.gridApi = jasmine.createSpyObj('GridApi', ['getSortModel']);
    (component.gridApi as any).getSortModel.and.returnValue([
      { colId: 'title', sort: 'asc' }
    ]);
    
    component.onSortChanged({} as any);
    
    expect(component.sortChanged.emit).toHaveBeenCalledWith({
      sortField: 'title',
      sortDirection: 'asc'
    });
  });

  it('should emit filterChanged event with filter model when filter changes', () => {
    spyOn(component.filterChanged, 'emit');
    
    // Setup grid API with filter model
    component.gridApi = jasmine.createSpyObj('GridApi', ['getFilterModel']);
    const filterModel = { title: { filter: 'test' } };
    (component.gridApi as any).getFilterModel.and.returnValue(filterModel);
    
    component.onFilterChanged({} as any);
    
    expect(component.filterChanged.emit).toHaveBeenCalledWith(filterModel);
  });

  it('should correctly format date/time with timezone', () => {
    const date = new Date('2023-06-12T10:00:00Z');
    const timezone = 'America/New_York';
    
    const formatted = component.formatDateTime(date, timezone);
    
    // The specific format depends on formatDateTimeWithTimezone implementation
    expect(formatted).toBeTruthy();
    expect(typeof formatted).toBe('string');
  });

  it('should return empty string when formatting null date', () => {
    const formatted = component.formatDateTime(null, 'UTC');
    expect(formatted).toBe('');
  });

  it('should open delete modal with the interaction data', () => {
    // Mock dialog.open method
    spyOn(component.dialog, 'open').and.returnValue({
      componentInstance: {
        interaction: null,
        deleted: jasmine.createSpyObj('EventEmitter', ['subscribe']),
        cancel: jasmine.createSpyObj('EventEmitter', ['subscribe'])
      }
    } as any);
    
    component.openDeleteModal(mockSearchResults.items[0]);
    
    expect(component.dialog.open).toHaveBeenCalled();
    expect(component.dialog.open.calls.mostRecent().returnValue.componentInstance.interaction)
      .toBe(mockSearchResults.items[0]);
  });

  it('should emit deleteInteraction event when modal confirms deletion', () => {
    spyOn(component.deleteInteraction, 'emit');
    
    // Mock dialog with deleted event
    spyOn(component.dialog, 'open').and.returnValue({
      componentInstance: {
        interaction: null,
        deleted: {
          subscribe: (fn: any) => {
            fn(); // Call the callback function immediately
            return { unsubscribe: () => {} };
          }
        },
        cancel: {
          subscribe: jasmine.createSpy('subscribe')
        }
      },
      close: jasmine.createSpy('close')
    } as any);
    
    const interaction = mockSearchResults.items[0];
    component.openDeleteModal(interaction);
    
    expect(component.deleteInteraction.emit).toHaveBeenCalledWith(interaction);
  });

  it('should close the modal when cancel event is emitted', () => {
    // Mock dialog with cancel event
    const mockDialogRef = {
      componentInstance: {
        interaction: null,
        deleted: jasmine.createSpyObj('EventEmitter', ['subscribe']),
        cancel: {
          subscribe: (fn: any) => {
            fn(); // Call the callback function immediately
            return { unsubscribe: () => {} };
          }
        }
      },
      close: jasmine.createSpy('close')
    };
    
    spyOn(component.dialog, 'open').and.returnValue(mockDialogRef as any);
    
    component.openDeleteModal(mockSearchResults.items[0]);
    
    expect(mockDialogRef.close).toHaveBeenCalled();
  });

  it('should handle no records condition correctly', () => {
    // With records
    component.searchResults = mockSearchResults;
    component.handleNoRecords();
    expect(component.hasNoRecords).toBe(false);
    
    // Without records
    component.searchResults = {
      ...mockSearchResults,
      items: []
    };
    component.handleNoRecords();
    expect(component.hasNoRecords).toBe(true);
  });

  it('should resize columns to fit when grid API is available', () => {
    component.gridApi = jasmine.createSpyObj('GridApi', ['sizeColumnsToFit']);
    
    component.sizeColumnsToFit();
    
    expect(component.gridApi.sizeColumnsToFit).toHaveBeenCalled();
  });

  it('should clean up subscriptions on destroy', () => {
    spyOn(component.destroy$, 'next');
    spyOn(component.destroy$, 'complete');
    
    // Create a mock subscription
    component.searchSubscription = jasmine.createSpyObj('Subscription', ['unsubscribe']);
    
    component.ngOnDestroy();
    
    expect(component.destroy$.next).toHaveBeenCalled();
    expect(component.destroy$.complete).toHaveBeenCalled();
    expect(component.searchSubscription.unsubscribe).toHaveBeenCalled();
  });
});