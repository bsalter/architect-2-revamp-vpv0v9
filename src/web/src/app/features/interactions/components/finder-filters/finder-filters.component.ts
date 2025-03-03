import {
  Component,
  OnInit,
  OnDestroy,
  Input,
  Output,
  EventEmitter,
  ViewChild
} from '@angular/core'; // v16.2.0
import {
  FormBuilder,
  FormGroup,
  FormArray,
  FormControl,
  Validators
} from '@angular/forms'; // v16.2.0
import {
  Subscription,
  Subject
} from 'rxjs'; // v7.8.1
import {
  takeUntil,
  debounceTime,
  distinctUntilChanged
} from 'rxjs/operators'; // v7.8.1

import {
  Filter,
  FilterOperator,
  FilterFieldType,
  FilterableInteractionFields,
  FilterField,
  SearchQuery,
  predefinedFilterFields
} from '../../models/filter.model';
import {
  InteractionType,
  INTERACTION_TYPE_OPTIONS
} from '../../models/interaction.model';
import { SearchService } from '../../services/search.service';
import { SiteSelectionService } from '../../../../core/auth/site-selection.service';
import { DateTimePickerComponent } from '../../../../shared/components/date-time-picker/date-time-picker.component';

/**
 * Component that implements the advanced filters panel for the Interaction Finder interface.
 * Provides UI controls for filtering interactions by various criteria including type, date range,
 * lead, and location, supporting comprehensive search capabilities with site-scoped data access.
 */
@Component({
  selector: 'app-finder-filters',
  templateUrl: './finder-filters.component.html',
  styleUrls: ['./finder-filters.component.scss']
})
export class FinderFiltersComponent implements OnInit, OnDestroy {
  /** Current active filters */
  @Input() filters: Filter[] = [];
  
  /** Event emitter for when filters change */
  @Output() filtersChange: EventEmitter<Filter[]> = new EventEmitter<Filter[]>();
  
  /** Event emitter for when the filter panel is closed */
  @Output() filterPanelClosed: EventEmitter<boolean> = new EventEmitter<boolean>();
  
  /** Form group containing all filter controls */
  filterForm: FormGroup;
  
  /** Available filter fields loaded from predefined configuration */
  availableFields: FilterField[] = [];
  
  /** Whether the filter panel is currently visible */
  isVisible: boolean = false;
  
  /** Whether a filtering operation is in progress */
  isLoading: boolean = false;
  
  /** Subject for unsubscribing from observables on component destruction */
  private destroy$: Subject<void> = new Subject<void>();
  
  /** Subscription to form value changes */
  private formSubscription: Subscription;
  
  /** Subscription to loading state changes */
  private loadingSubscription: Subscription;
  
  /** Current site ID for site-scoped filtering */
  private currentSiteId: number;

  /**
   * Creates an instance of the FinderFiltersComponent.
   * 
   * @param fb FormBuilder for creating reactive forms
   * @param searchService Service for handling search operations
   * @param siteService Service for retrieving site context
   */
  constructor(
    private fb: FormBuilder,
    private searchService: SearchService,
    private siteService: SiteSelectionService
  ) {
    this.filtersChange = new EventEmitter<Filter[]>();
    this.filterPanelClosed = new EventEmitter<boolean>();
    this.destroy$ = new Subject<void>();
    
    // Load available filter fields
    this.availableFields = predefinedFilterFields;
    
    // Filter panel is initially hidden
    this.isVisible = false;
    
    // Get current site ID for site-scoped filtering
    this.currentSiteId = this.siteService.getCurrentSiteId();
  }

  /**
   * Initializes the component, sets up form controls, and subscribes to relevant observables.
   */
  ngOnInit(): void {
    // Initialize the form
    this.initForm();
    
    // Subscribe to loading state changes
    this.loadingSubscription = this.searchService.loading$
      .pipe(takeUntil(this.destroy$))
      .subscribe(loading => {
        this.isLoading = loading;
      });
    
    // Subscribe to form value changes to apply filters
    this.formSubscription = this.filterForm.valueChanges
      .pipe(
        takeUntil(this.destroy$),
        debounceTime(300),
        distinctUntilChanged()
      )
      .subscribe(() => {
        // Don't apply filters while form is invalid
        if (this.filterForm.valid) {
          this.applyFilters();
        }
      });
    
    // If filters are provided via input, apply them to the form
    if (this.filters && this.filters.length > 0) {
      this.filtersToForm(this.filters);
    }
  }

  /**
   * Cleans up subscriptions when component is destroyed.
   */
  ngOnDestroy(): void {
    // Complete the destroy subject to unsubscribe from all subscriptions
    this.destroy$.next();
    this.destroy$.complete();
    
    // Manually unsubscribe from any subscriptions not using takeUntil
    if (this.formSubscription) {
      this.formSubscription.unsubscribe();
    }
    
    if (this.loadingSubscription) {
      this.loadingSubscription.unsubscribe();
    }
  }

  /**
   * Initializes the reactive form for the filter controls.
   */
  initForm(): void {
    this.filterForm = this.fb.group({
      // Type filter as checkbox group
      type: this.fb.group({
        [InteractionType.MEETING]: [true],
        [InteractionType.CALL]: [true],
        [InteractionType.EMAIL]: [true],
        [InteractionType.OTHER]: [false]
      }),
      
      // Date range filters
      dateRange: this.fb.group({
        fromDate: [null],
        toDate: [null]
      }),
      
      // Lead filter
      lead: [''],
      
      // Location filter
      location: ['']
    });
  }

  /**
   * Applies the current filter form values and emits the filter change event.
   */
  applyFilters(): void {
    if (!this.filterForm.valid) {
      return;
    }
    
    // Convert form values to Filter array
    const formValues = this.filterForm.value;
    const filters = this.formToFilters(formValues);
    
    // Emit the filter change event
    this.filtersChange.emit(filters);
    
    // Update internal filters property
    this.filters = filters;
  }

  /**
   * Clears all filters and resets the form.
   */
  clearFilters(): void {
    // Reset form to default values
    this.filterForm.reset({
      type: {
        [InteractionType.MEETING]: true,
        [InteractionType.CALL]: true,
        [InteractionType.EMAIL]: true,
        [InteractionType.OTHER]: false
      },
      dateRange: {
        fromDate: null,
        toDate: null
      },
      lead: '',
      location: ''
    });
    
    // Clear internal filters array
    this.filters = [];
    
    // Emit empty filters
    this.filtersChange.emit([]);
  }

  /**
   * Toggles the visibility of the filter panel.
   */
  toggleFilterPanel(): void {
    this.isVisible = !this.isVisible;
    
    // If closing the panel, emit event
    if (!this.isVisible) {
      this.filterPanelClosed.emit(true);
    }
  }

  /**
   * Closes the filter panel.
   */
  closeFilterPanel(): void {
    this.isVisible = false;
    this.filterPanelClosed.emit(true);
  }

  /**
   * Gets the current value of a filter by field name.
   * 
   * @param fieldName The field name to get the value for
   * @returns The filter value or null if not found
   */
  getFilterValue(fieldName: string): any {
    if (!this.filters || this.filters.length === 0) {
      return null;
    }
    
    const filter = this.filters.find(f => f.field === fieldName);
    return filter ? filter.value : null;
  }

  /**
   * Gets options for a select-type filter field.
   * 
   * @param fieldName The field name to get options for
   * @returns Array of options for the field
   */
  getFieldOptions(fieldName: string): any[] {
    const field = this.availableFields.find(f => f.field === fieldName);
    return field && field.options ? field.options : [];
  }

  /**
   * Converts form values to Filter[] format.
   * 
   * @param formValues Values from the filterForm
   * @returns Array of Filter objects
   */
  formToFilters(formValues: any): Filter[] {
    const filters: Filter[] = [];
    
    // Process type filter checkboxes
    const typeValues = formValues.type;
    const selectedTypes = Object.keys(typeValues)
      .filter(type => typeValues[type])
      .map(type => type);
    
    if (selectedTypes.length > 0 && selectedTypes.length < 4) {
      // Only add type filter if not all options are selected (which would be the same as no filter)
      filters.push({
        field: FilterableInteractionFields.TYPE,
        operator: FilterOperator.EQUALS,
        value: selectedTypes
      });
    }
    
    // Process date range
    if (formValues.dateRange) {
      const { fromDate, toDate } = formValues.dateRange;
      
      if (fromDate) {
        filters.push({
          field: FilterableInteractionFields.START_DATETIME,
          operator: FilterOperator.GREATER_THAN_OR_EQUAL,
          value: fromDate
        });
      }
      
      if (toDate) {
        filters.push({
          field: FilterableInteractionFields.END_DATETIME,
          operator: FilterOperator.LESS_THAN_OR_EQUAL,
          value: toDate
        });
      }
    }
    
    // Process lead filter
    if (formValues.lead) {
      filters.push({
        field: FilterableInteractionFields.LEAD,
        operator: FilterOperator.CONTAINS,
        value: formValues.lead
      });
    }
    
    // Process location filter
    if (formValues.location) {
      filters.push({
        field: FilterableInteractionFields.LOCATION,
        operator: FilterOperator.CONTAINS,
        value: formValues.location
      });
    }
    
    return filters;
  }

  /**
   * Applies Filter[] values to the form controls.
   * 
   * @param filters Array of Filter objects to apply to the form
   */
  filtersToForm(filters: Filter[]): void {
    // Initialize default form values
    const formValues = {
      type: {
        [InteractionType.MEETING]: true,
        [InteractionType.CALL]: true,
        [InteractionType.EMAIL]: true,
        [InteractionType.OTHER]: true
      },
      dateRange: {
        fromDate: null,
        toDate: null
      },
      lead: '',
      location: ''
    };
    
    // Process each filter and update form values accordingly
    for (const filter of filters) {
      switch (filter.field) {
        case FilterableInteractionFields.TYPE:
          // For type filter, reset all to false first, then set selected ones to true
          if (Array.isArray(filter.value)) {
            Object.keys(formValues.type).forEach(key => {
              formValues.type[key] = false;
            });
            
            filter.value.forEach(type => {
              formValues.type[type] = true;
            });
          } else {
            // Handle case where a single type is selected
            Object.keys(formValues.type).forEach(key => {
              formValues.type[key] = key === filter.value;
            });
          }
          break;
          
        case FilterableInteractionFields.START_DATETIME:
          if (filter.operator === FilterOperator.GREATER_THAN_OR_EQUAL || 
              filter.operator === FilterOperator.GREATER_THAN) {
            formValues.dateRange.fromDate = filter.value;
          }
          break;
          
        case FilterableInteractionFields.END_DATETIME:
          if (filter.operator === FilterOperator.LESS_THAN_OR_EQUAL ||
              filter.operator === FilterOperator.LESS_THAN) {
            formValues.dateRange.toDate = filter.value;
          }
          break;
          
        case FilterableInteractionFields.LEAD:
          formValues.lead = filter.value;
          break;
          
        case FilterableInteractionFields.LOCATION:
          formValues.location = filter.value;
          break;
      }
    }
    
    // Update the form without triggering value change events
    this.filterForm.patchValue(formValues, { emitEvent: false });
    
    // Mark form controls as pristine and untouched
    this.filterForm.markAsPristine();
    this.filterForm.markAsUntouched();
  }

  /**
   * Handles selection of the 'from date' in date range filter.
   * 
   * @param date Selected date
   */
  onFromDateSelected(date: Date): void {
    // Update the formControl
    this.filterForm.get('dateRange.fromDate').setValue(date);
    
    // If toDate exists and is before fromDate, clear toDate
    const toDate = this.filterForm.get('dateRange.toDate').value;
    if (toDate && date && toDate < date) {
      this.filterForm.get('dateRange.toDate').setValue(null);
    }
  }

  /**
   * Handles selection of the 'to date' in date range filter.
   * 
   * @param date Selected date
   */
  onToDateSelected(date: Date): void {
    // Update the formControl
    this.filterForm.get('dateRange.toDate').setValue(date);
    
    // If fromDate exists and is after toDate, adjust fromDate
    const fromDate = this.filterForm.get('dateRange.fromDate').value;
    if (fromDate && date && fromDate > date) {
      this.filterForm.get('dateRange.fromDate').setValue(date);
    }
  }

  /**
   * Checks if there are any active filters.
   * 
   * @returns True if filters are active
   */
  hasActiveFilters(): boolean {
    return this.filters && this.filters.length > 0;
  }

  /**
   * Gets the count of active filters.
   * 
   * @returns Number of active filters
   */
  getActiveFilterCount(): number {
    return this.filters ? this.filters.length : 0;
  }
}