import { Component, Input, Output, EventEmitter, OnChanges, SimpleChanges } from '@angular/core'; // Angular 16.2.0
import { faAngleLeft, faAngleRight, faAngleDoubleLeft, faAngleDoubleRight } from '@fortawesome/free-solid-svg-icons'; // 6.4.0
import { SearchResultsMetadata } from '../../../features/interactions/models/search-results.model';

/**
 * Reusable component that provides pagination controls with configurable display options
 * and accessibility features for navigating through paginated data sets in the application.
 */
@Component({
  selector: 'app-pagination',
  templateUrl: './pagination.component.html',
  styleUrls: ['./pagination.component.scss']
})
export class PaginationComponent implements OnChanges {
  /**
   * Current active page (1-based indexing)
   */
  @Input() currentPage: number = 1;
  
  /**
   * Total number of pages available
   */
  @Input() totalPages: number = 1;
  
  /**
   * Maximum number of page numbers to display at once
   * Controls how many page buttons are shown before using ellipsis
   */
  @Input() maxVisiblePages: number = 5;
  
  /**
   * Event emitted when user selects a different page
   */
  @Output() pageChange = new EventEmitter<number>();
  
  /**
   * Array of page numbers currently visible in the pagination control
   */
  visiblePages: number[] = [];
  
  /**
   * Whether to show ellipsis at the beginning of the page numbers
   */
  showStartEllipsis: boolean = false;
  
  /**
   * Whether to show ellipsis at the end of the page numbers
   */
  showEndEllipsis: boolean = false;
  
  // FontAwesome icons for navigation buttons
  faAngleLeft = faAngleLeft;
  faAngleRight = faAngleRight;
  faAngleDoubleLeft = faAngleDoubleLeft;
  faAngleDoubleRight = faAngleDoubleRight;
  
  /**
   * Initializes the component and assigns Font Awesome icons
   */
  constructor() {}
  
  /**
   * Recalculates visible pages whenever inputs change
   * @param changes Changes to the component inputs
   */
  ngOnChanges(changes: SimpleChanges): void {
    // Ensure currentPage is within valid range
    if (this.currentPage < 1) {
      this.currentPage = 1;
    } else if (this.currentPage > this.totalPages) {
      this.currentPage = this.totalPages > 0 ? this.totalPages : 1;
    }
    
    // Ensure totalPages is at least 1
    if (this.totalPages < 1) {
      this.totalPages = 1;
    }
    
    this.calculateVisiblePages();
  }
  
  /**
   * Calculates which page numbers should be visible in the pagination control
   * based on current page and configured maxVisiblePages.
   * Also determines when to show ellipsis for large page counts.
   */
  calculateVisiblePages(): void {
    this.visiblePages = [];
    
    if (this.totalPages <= this.maxVisiblePages) {
      // If we have fewer pages than the max visible, show all pages
      for (let i = 1; i <= this.totalPages; i++) {
        this.visiblePages.push(i);
      }
      this.showStartEllipsis = false;
      this.showEndEllipsis = false;
    } else {
      // Calculate the range of pages to display
      let startPage: number;
      let endPage: number;
      
      const halfVisible = Math.floor(this.maxVisiblePages / 2);
      
      if (this.currentPage <= halfVisible + 1) {
        // We're near the start
        startPage = 1;
        endPage = this.maxVisiblePages;
        this.showStartEllipsis = false;
        this.showEndEllipsis = true;
      } else if (this.currentPage >= this.totalPages - halfVisible) {
        // We're near the end
        startPage = this.totalPages - this.maxVisiblePages + 1;
        endPage = this.totalPages;
        this.showStartEllipsis = true;
        this.showEndEllipsis = false;
      } else {
        // We're in the middle
        startPage = this.currentPage - halfVisible;
        endPage = this.currentPage + halfVisible;
        this.showStartEllipsis = true;
        this.showEndEllipsis = true;
      }
      
      // Create the array of visible page numbers
      for (let i = startPage; i <= endPage; i++) {
        this.visiblePages.push(i);
      }
    }
  }
  
  /**
   * Handles navigation to a specific page
   * @param page The page number to navigate to
   */
  goToPage(page: number): void {
    if (page < 1 || page > this.totalPages || page === this.currentPage) {
      return;
    }
    
    this.currentPage = page;
    this.pageChange.emit(page);
  }
  
  /**
   * Validates that the current page is within the valid range
   * @returns True if current page is valid
   */
  isCurrentPageValid(): boolean {
    return typeof this.currentPage === 'number' && 
           this.currentPage >= 1 && 
           this.currentPage <= this.totalPages;
  }
}