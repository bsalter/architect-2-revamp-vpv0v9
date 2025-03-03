import { Component, Input, Output, EventEmitter, OnInit, OnDestroy } from '@angular/core'; // @angular/core v16.2.0
import { FormControl } from '@angular/forms'; // @angular/forms v16.2.0
import { Subject } from 'rxjs'; // rxjs v7.8.1
import { debounceTime, distinctUntilChanged, takeUntil } from 'rxjs/operators'; // rxjs/operators v7.8.1
import { isEmpty } from '../../../core/utils/string-utils';

/**
 * A reusable search input component with debounced search functionality,
 * clear button, and accessibility features.
 * 
 * This component is used throughout the application, particularly in
 * the Interaction Finder interface to enable users to search across
 * interaction records.
 */
@Component({
  selector: 'app-search-input',
  templateUrl: './search-input.component.html',
  styleUrls: ['./search-input.component.scss']
})
export class SearchInputComponent implements OnInit, OnDestroy {
  /**
   * Placeholder text for the search input
   */
  @Input() placeholder = 'Search interactions...';

  /**
   * Initial search term value
   */
  @Input() searchTerm = '';

  /**
   * Time in milliseconds to wait before emitting search event after input changes
   */
  @Input() debounceTime = 300;

  /**
   * Event emitted when search term changes (debounced)
   */
  @Output() search = new EventEmitter<string>();

  /**
   * Event emitted when search is cleared
   */
  @Output() cleared = new EventEmitter<void>();

  /**
   * Form control for the search input
   */
  searchControl = new FormControl('');

  /**
   * Subject for managing component unsubscription
   */
  private destroy$ = new Subject<void>();

  /**
   * Initializes the component and sets up the debounced search
   */
  ngOnInit(): void {
    // Set initial value from input if provided
    if (!isEmpty(this.searchTerm)) {
      this.searchControl.setValue(this.searchTerm, { emitEvent: false });
    }
    
    // Subscribe to value changes with debounce
    this.searchControl.valueChanges.pipe(
      debounceTime(this.debounceTime),
      distinctUntilChanged(),
      takeUntil(this.destroy$)
    ).subscribe(value => {
      // Ensure value is always a string, even if null or undefined
      this.search.emit(value || '');
    });
  }

  /**
   * Cleans up resources when component is destroyed
   */
  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * Manually triggers search with current input value
   * (used for enter key press)
   */
  onSearch(): void {
    const value = this.searchControl.value;
    this.search.emit(value || '');
  }

  /**
   * Clears the search input and emits cleared event
   * 
   * @param event - The DOM event that triggered the clear action
   */
  clearSearch(event: Event): void {
    // Prevent event propagation to avoid unwanted behavior
    event.stopPropagation();
    
    // Reset search control value
    this.searchControl.setValue('');
    
    // Emit cleared event for parent components
    this.cleared.emit();
  }
}