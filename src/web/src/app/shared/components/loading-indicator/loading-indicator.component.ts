import { Component, Input } from '@angular/core'; // v16.2.0

/**
 * A configurable loading indicator component that provides visual feedback
 * during asynchronous operations throughout the application.
 * 
 * Usage example:
 * <app-loading-indicator 
 *   [show]="isLoading"
 *   [text]="'Saving interaction...'" 
 *   [size]="'large'"
 *   [fullscreen]="true">
 * </app-loading-indicator>
 */
@Component({
  selector: 'app-loading-indicator',
  templateUrl: './loading-indicator.component.html',
  styleUrls: ['./loading-indicator.component.scss']
})
export class LoadingIndicatorComponent {
  /**
   * Controls the visibility of the loading indicator
   */
  @Input() show: boolean = true;

  /**
   * Text message to display while loading
   */
  @Input() text: string = 'Loading...';

  /**
   * Toggle text visibility alongside the spinner
   */
  @Input() showText: boolean = true;

  /**
   * Size of the spinner (small, medium, large)
   */
  @Input() size: string = 'medium';

  /**
   * Display over the entire screen with a backdrop
   */
  @Input() fullscreen: boolean = false;

  /**
   * Display as an inline element instead of block
   */
  @Input() inline: boolean = false;

  /**
   * Accessibility label for screen readers
   */
  @Input() ariaLabel: string = 'Loading content, please wait';

  /**
   * Default constructor for the loading indicator component
   */
  constructor() { }

  /**
   * Returns the CSS class for the spinner based on the size input
   * @returns CSS class name for spinner size
   */
  getSizeClass(): string {
    switch (this.size) {
      case 'small':
        return 'spinner-sm';
      case 'large':
        return 'spinner-lg';
      case 'medium':
      default:
        return 'spinner-md';
    }
  }

  /**
   * Returns the CSS classes for the container based on display mode inputs
   * @returns Object with class names as keys and boolean values
   */
  getContainerClasses(): { [key: string]: boolean } {
    return {
      'loading-indicator-container': true,
      'fullscreen': this.fullscreen,
      'inline': this.inline
    };
  }
}