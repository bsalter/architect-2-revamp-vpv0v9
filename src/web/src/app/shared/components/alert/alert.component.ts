import { Component, Input, Output, EventEmitter, OnInit, OnDestroy } from '@angular/core';
import { trigger, transition, style, animate } from '@angular/animations'; // v16.2.0
import { sanitizeHtml } from '../../../core/utils/string-utils';

/**
 * Alert component for displaying user feedback messages
 * 
 * This component provides standardized alert messages with different severity levels
 * (success, warning, error/danger, info) for providing feedback to users across the application.
 * It supports features like dismissible alerts, different visualization styles, and programmatic control.
 * 
 * Accessibility: Component implements WCAG 2.1 AA standards with proper ARIA attributes,
 * keyboard navigation, and focus management.
 */
@Component({
  selector: 'app-alert',
  templateUrl: './alert.component.html',
  styleUrls: ['./alert.component.scss'],
  animations: [
    trigger('fadeInOut', [
      transition(':enter', [
        style({ opacity: 0 }),
        animate('300ms ease-in', style({ opacity: 1 }))
      ]),
      transition(':leave', [
        animate('300ms ease-out', style({ opacity: 0 }))
      ])
    ])
  ]
})
export class AlertComponent implements OnInit, OnDestroy {
  /**
   * Type of alert to display
   * Possible values: 'success', 'warning', 'danger', 'info' (default)
   */
  @Input() type = 'info';
  
  /**
   * Alert message content
   * HTML content will be sanitized before display
   */
  @Input() message: string;
  
  /**
   * Whether the alert can be dismissed by the user
   * Default: false
   */
  @Input() dismissible = false;
  
  /**
   * Time in milliseconds after which the alert will automatically dismiss
   * Set to 0 (default) to disable auto-dismissal
   */
  @Input() autoDismissTime = 0;
  
  /**
   * Event emitted when the alert is closed either by user action or auto-dismissal
   */
  @Output() closed = new EventEmitter<void>();
  
  /**
   * Reference to auto-dismiss timeout for cleanup
   */
  private autoDismissTimeout: any;
  
  /**
   * Controls the visibility of the alert
   * Used for animation states
   */
  visible = true;
  
  /**
   * Initializes the component with default properties
   */
  constructor() {
    // Initialize component with default properties
  }
  
  /**
   * Lifecycle hook that runs after component initialization
   * Sanitizes message content and sets up auto-dismiss if enabled
   */
  ngOnInit(): void {
    // If message exists, sanitize HTML content with sanitizeHtml utility
    if (this.message) {
      this.message = sanitizeHtml(this.message);
    }
    
    // Set up auto-dismiss timeout if autoDismissTime is greater than 0
    this.setupAutoDismiss();
  }
  
  /**
   * Lifecycle hook that runs when component is destroyed
   * Cleans up any active timeouts to prevent memory leaks
   */
  ngOnDestroy(): void {
    // Clear any active auto-dismiss timeout to prevent memory leaks
    if (this.autoDismissTimeout) {
      clearTimeout(this.autoDismissTimeout);
    }
  }
  
  /**
   * Closes the alert and emits an event to notify parent components
   */
  closeAlert(): void {
    // Set visible flag to false
    this.visible = false;
    
    // Emit closed event for parent components to handle
    this.closed.emit();
    
    // Clear any active auto-dismiss timeout
    if (this.autoDismissTimeout) {
      clearTimeout(this.autoDismissTimeout);
    }
  }
  
  /**
   * Sets up the auto-dismiss timeout if enabled
   * Private helper method used during initialization
   */
  private setupAutoDismiss(): void {
    // Check if autoDismissTime is greater than 0
    if (this.autoDismissTime > 0) {
      // If valid, set a timeout to call closeAlert after specified time
      this.autoDismissTimeout = setTimeout(() => {
        this.closeAlert();
      }, this.autoDismissTime);
    }
  }
}