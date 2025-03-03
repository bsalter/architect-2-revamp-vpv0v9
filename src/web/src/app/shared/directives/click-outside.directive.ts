import { Directive, ElementRef, EventEmitter, HostListener, Output } from '@angular/core'; // @angular/core 16.2.0

/**
 * Directive that detects clicks outside of an element and emits an event.
 * 
 * Used for:
 * - Closing dropdowns when clicking elsewhere on the page
 * - Dismissing modals by clicking outside
 * - Hiding context menus when clicking in other areas
 * 
 * Usage:
 * ```html
 * <div appClickOutside (clickOutside)="onClickOutside()">Content</div>
 * ```
 */
@Directive({
  selector: '[appClickOutside]'
})
export class ClickOutsideDirective {
  /**
   * Event emitted when a click occurs outside the host element
   */
  @Output() clickOutside = new EventEmitter<void>();

  /**
   * Constructor
   * @param elementRef Reference to the element this directive is attached to
   */
  constructor(private elementRef: ElementRef) {}

  /**
   * Handles document click events and determines if they occurred 
   * outside the host element
   * 
   * @param event The click event
   */
  @HostListener('document:click', ['$event'])
  onClick(event: Event): void {
    // Get the element that was clicked
    const clickedElement = event.target as HTMLElement;
    
    // Check if the clicked element is the host element or is contained within it
    const isInside = this.elementRef.nativeElement.contains(clickedElement);
    
    // If the click was outside the element, emit the event
    if (!isInside) {
      this.clickOutside.emit();
    }
  }
}