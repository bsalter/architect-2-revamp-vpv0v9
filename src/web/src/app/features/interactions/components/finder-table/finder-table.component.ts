import { Component, OnInit, OnDestroy, ViewChild, Input, Output, EventEmitter } from '@angular/core';
import { Router } from '@angular/router'; // v16.2.0
import { MatDialog } from '@angular/material/dialog'; // v16.2.0
import { 
  ColDef, 
  GridOptions, 
  GridReadyEvent, 
  RowSelectedEvent, 
  CellClickedEvent, 
  GridApi, 
  ValueFormatterParams, 
  FilterChangedEvent, 
  SortChangedEvent 
} from 'ag-grid-community'; // v30.0.3
import { Subject, Subscription, takeUntil } from 'rxjs'; // v7.8.1
import { format } from 'date-fns'; // v2.30.0

import { Interaction, InteractionType } from '../../models/interaction.model';
import { SearchResults, SearchResultItem, SearchResultsMetadata } from '../../models/search-results.model';
import { SearchService } from '../../services/search.service';
import { InteractionService } from '../../services/interaction.service';
import { SiteSelectionService } from '../../../../core/auth/site-selection.service';
import { InteractionDeleteModalComponent } from '../interaction-delete-modal/interaction-delete-modal.component';
import { formatDateTimeWithTimezone } from '../../../../core/utils/datetime-utils';

/**
 * Component that implements the tabular view for displaying, sorting, and managing Interaction records.
 * Uses AG Grid to provide a high-performance table with advanced features including
 * sorting, filtering, and row selection.
 */
@Component({
  selector: 'app-finder-table',
  templateUrl: './finder-table.component.html',
  styleUrls: ['./finder-table.component.scss']
})
export class FinderTableComponent implements OnInit, OnDestroy {
  /** Search results data for the table */
  @Input() searchResults: SearchResults;
  
  /** Event emitted when a user wants to view an interaction */
  @Output() viewInteraction = new EventEmitter<number>();
  
  /** Event emitted when a user wants to edit an interaction */
  @Output() editInteraction = new EventEmitter<number>();
  
  /** Event emitted when a user wants to delete an interaction */
  @Output() deleteInteraction = new EventEmitter<Interaction>();
  
  /** Event emitted when sort criteria changes */
  @Output() sortChanged = new EventEmitter<object>();
  
  /** Event emitted when filter criteria changes */
  @Output() filterChanged = new EventEmitter<object>();
  
  /** Reference to the AG Grid component */
  @ViewChild('agGrid') agGridElement;
  
  /** Column definitions for AG Grid */
  columnDefs: ColDef[];
  
  /** Grid configuration options */
  gridOptions: GridOptions;
  
  /** Reference to the AG Grid API */
  gridApi: GridApi;
  
  /** Flag indicating whether there are no records to display */
  hasNoRecords = false;
  
  /** The current site ID for site-scoped access */
  currentSiteId: number;
  
  /** Subject used to clean up subscriptions on component destruction */
  destroy$ = new Subject<void>();
  
  /** Subscription to search results */
  searchSubscription: Subscription;
  
  /**
   * Creates an instance of FinderTableComponent
   * 
   * @param router Router for navigation
   * @param dialog Material dialog service for delete confirmations
   * @param searchService Service for retrieving and searching interactions
   * @param interactionService Service for interaction CRUD operations
   * @param siteService Service for accessing site context
   */
  constructor(
    private router: Router,
    private dialog: MatDialog,
    private searchService: SearchService,
    private interactionService: InteractionService,
    private siteService: SiteSelectionService
  ) {
    // Get current site ID for site-scoped access
    this.currentSiteId = this.siteService.getCurrentSiteId();
    
    // Initialize column definitions
    this.initializeColumnDefs();
    
    // Initialize grid options
    this.gridOptions = {
      defaultColDef: {
        sortable: true,
        filter: true,
        resizable: true,
        minWidth: 100
      },
      rowSelection: 'single',
      suppressCellFocus: false,
      animateRows: true,
      pagination: true,
      paginationAutoPageSize: false,
      suppressPaginationPanel: true, // We'll handle pagination externally
      rowData: [],
      onGridReady: this.onGridReady.bind(this),
      onRowSelected: this.onRowSelected.bind(this),
      onCellClicked: this.onCellClicked.bind(this),
      onFilterChanged: this.onFilterChanged.bind(this),
      onSortChanged: this.onSortChanged.bind(this),
      getContextMenuItems: this.getContextMenuItems.bind(this),
      suppressRowClickSelection: false,
      enableCellTextSelection: true,
      suppressLoadingOverlay: true,
      suppressNoRowsOverlay: true
    };
  }
  
  /**
   * Lifecycle hook that initializes the component
   */
  ngOnInit(): void {
    // Subscribe to search results
    this.searchSubscription = this.searchService.searchResults$
      .pipe(takeUntil(this.destroy$))
      .subscribe(results => {
        if (results) {
          // Update table with search results
          if (this.gridApi) {
            this.gridApi.setRowData(results.items || []);
          }
          
          // Check if we have any records
          this.handleNoRecords();
        }
      });
    
    // Initialize grid if we already have search results
    if (this.searchResults) {
      // Update table with initial search results
      if (this.gridApi) {
        this.gridApi.setRowData(this.searchResults.items || []);
      }
      
      // Check if we have any records
      this.handleNoRecords();
    }
  }
  
  /**
   * Lifecycle hook for cleanup when component is destroyed
   */
  ngOnDestroy(): void {
    // Complete the destroy subject to unsubscribe from all observables
    this.destroy$.next();
    this.destroy$.complete();
    
    // Unsubscribe from search subscription if it exists
    if (this.searchSubscription) {
      this.searchSubscription.unsubscribe();
    }
  }
  
  /**
   * Sets up the column definitions for AG Grid
   */
  initializeColumnDefs(): void {
    this.columnDefs = [
      {
        headerName: 'Title',
        field: 'title',
        filter: 'agTextColumnFilter',
        sortable: true,
        flex: 2,
        minWidth: 200,
        filterParams: {
          filterOptions: ['contains', 'equals', 'startsWith', 'endsWith'],
          suppressAndOrCondition: true
        }
      },
      {
        headerName: 'Type',
        field: 'type',
        filter: 'agSetColumnFilter',
        sortable: true,
        flex: 1,
        minWidth: 120,
        filterParams: {
          values: Object.values(InteractionType)
        },
        cellClass: 'type-cell'
      },
      {
        headerName: 'Lead',
        field: 'lead',
        filter: 'agTextColumnFilter',
        sortable: true,
        flex: 1,
        minWidth: 150
      },
      {
        headerName: 'Date/Time',
        field: 'startDatetime',
        filter: 'agDateColumnFilter',
        sortable: true,
        flex: 1.5,
        minWidth: 180,
        valueFormatter: params => this.formatDateTime(params.value, params.data?.timezone),
        filterParams: {
          comparator: (filterLocalDateAtMidnight, cellValue) => {
            const dateAsString = cellValue;
            if (dateAsString == null) return -1;
            
            const cellDate = new Date(dateAsString);
            const filterDate = new Date(filterLocalDateAtMidnight);
            
            if (cellDate < filterDate) {
              return -1;
            } else if (cellDate > filterDate) {
              return 1;
            }
            return 0;
          }
        }
      },
      {
        headerName: 'Location',
        field: 'location',
        filter: 'agTextColumnFilter',
        sortable: true,
        flex: 1.5,
        minWidth: 150,
        filterParams: {
          filterOptions: ['contains', 'equals', 'startsWith'],
          suppressAndOrCondition: true
        }
      },
      {
        headerName: 'Actions',
        field: 'id',
        sortable: false,
        filter: false,
        width: 120,
        minWidth: 120,
        pinned: 'right',
        cellRenderer: params => {
          const container = document.createElement('div');
          container.className = 'action-buttons';
          
          // View button
          const viewBtn = document.createElement('button');
          viewBtn.innerHTML = '<i class="material-icons">visibility</i>';
          viewBtn.className = 'btn-action btn-view';
          viewBtn.title = 'View';
          viewBtn.addEventListener('click', e => {
            e.stopPropagation();
            this.viewInteraction.emit(params.value);
          });
          
          // Edit button
          const editBtn = document.createElement('button');
          editBtn.innerHTML = '<i class="material-icons">edit</i>';
          editBtn.className = 'btn-action btn-edit';
          editBtn.title = 'Edit';
          editBtn.addEventListener('click', e => {
            e.stopPropagation();
            this.editInteraction.emit(params.value);
          });
          
          // Delete button
          const deleteBtn = document.createElement('button');
          deleteBtn.innerHTML = '<i class="material-icons">delete</i>';
          deleteBtn.className = 'btn-action btn-delete';
          deleteBtn.title = 'Delete';
          deleteBtn.addEventListener('click', e => {
            e.stopPropagation();
            this.openDeleteModal(params.data);
          });
          
          container.appendChild(viewBtn);
          container.appendChild(editBtn);
          container.appendChild(deleteBtn);
          
          return container;
        }
      }
    ];
  }
  
  /**
   * Handler for AG Grid initialization event
   * 
   * @param params Grid ready event parameters
   */
  onGridReady(params: GridReadyEvent): void {
    this.gridApi = params.api;
    
    // Set initial row data if available
    if (this.searchResults && this.searchResults.items) {
      this.gridApi.setRowData(this.searchResults.items);
    }
    
    // Resize columns to fit the available width
    this.sizeColumnsToFit();
    
    // Handle window resize to adjust grid size
    window.addEventListener('resize', () => {
      setTimeout(() => {
        this.sizeColumnsToFit();
      });
    });
  }
  
  /**
   * Handler for row selection events
   * 
   * @param event Row selected event
   */
  onRowSelected(event: RowSelectedEvent): void {
    if (event.node.isSelected()) {
      const selectedData = event.node.data;
      // Emit view event when row is selected
      this.viewInteraction.emit(selectedData.id);
    }
  }
  
  /**
   * Handler for cell click events, especially for action buttons
   * 
   * @param event Cell clicked event
   */
  onCellClicked(event: CellClickedEvent): void {
    // Handle action column clicks to prevent row selection
    if (event.column.getColId() === 'id') {
      // Prevent row selection when clicking action buttons
      event.node.setSelected(false);
    }
  }
  
  /**
   * Handler for column sorting changes
   * 
   * @param event Sort changed event
   */
  onSortChanged(event: SortChangedEvent): void {
    if (this.gridApi) {
      const sortModel = this.gridApi.getSortModel();
      if (sortModel && sortModel.length > 0) {
        const sortParams = {
          sortField: sortModel[0].colId,
          sortDirection: sortModel[0].sort
        };
        this.sortChanged.emit(sortParams);
      } else {
        // Clear sort
        this.sortChanged.emit({});
      }
    }
  }
  
  /**
   * Handler for column filter changes
   * 
   * @param event Filter changed event
   */
  onFilterChanged(event: FilterChangedEvent): void {
    if (this.gridApi) {
      const filterModel = this.gridApi.getFilterModel();
      this.filterChanged.emit(filterModel);
    }
  }
  
  /**
   * Formats date and time for display in grid
   * 
   * @param date Date to format
   * @param timezone Timezone for the date
   * @returns Formatted date/time string
   */
  formatDateTime(date: Date, timezone: string): string {
    if (!date) return '';
    return formatDateTimeWithTimezone(new Date(date), 'MMM d, yyyy h:mm a', timezone || 'UTC');
  }
  
  /**
   * Opens the delete confirmation dialog for an interaction
   * 
   * @param interaction The interaction to delete
   */
  openDeleteModal(interaction: Interaction): void {
    const dialogRef = this.dialog.open(InteractionDeleteModalComponent, {
      width: '500px'
    });
    
    // Set the interaction input property
    dialogRef.componentInstance.interaction = interaction;
    
    // Subscribe to events
    dialogRef.componentInstance.deleted.subscribe(() => {
      // Emit delete event to parent component
      this.deleteInteraction.emit(interaction);
      dialogRef.close();
    });
    
    dialogRef.componentInstance.cancel.subscribe(() => {
      dialogRef.close();
    });
  }
  
  /**
   * Provides custom context menu for right-click on grid rows
   * 
   * @param params Context menu parameters
   * @returns Menu items array
   */
  getContextMenuItems(params: any): any[] {
    const items = [];
    
    if (params.node) {
      const interaction = params.node.data;
      
      items.push({
        name: 'View Interaction',
        icon: '<i class="material-icons">visibility</i>',
        action: () => {
          this.viewInteraction.emit(interaction.id);
        }
      });
      
      items.push({
        name: 'Edit Interaction',
        icon: '<i class="material-icons">edit</i>',
        action: () => {
          this.editInteraction.emit(interaction.id);
        }
      });
      
      items.push('separator');
      
      items.push({
        name: 'Delete Interaction',
        icon: '<i class="material-icons">delete</i>',
        action: () => {
          this.openDeleteModal(interaction);
        }
      });
    }
    
    return items;
  }
  
  /**
   * Handles display when no records are found
   */
  handleNoRecords(): void {
    const hasItems = this.searchResults && 
                     this.searchResults.items && 
                     this.searchResults.items.length > 0;
    this.hasNoRecords = !hasItems;
  }
  
  /**
   * Resizes columns to fit available space
   */
  sizeColumnsToFit(): void {
    if (this.gridApi) {
      this.gridApi.sizeColumnsToFit();
    }
  }
}