import { Directive, Input, Output, EventEmitter, OnInit, OnDestroy, ElementRef, Renderer2 } from '@angular/core'; // v16.2.0
import { Subscription } from 'rxjs'; // v7.8.1
import { UserContextService } from '../../core/auth/user-context.service';
import { SiteContext } from '../../features/sites/models/site.model';

/**
 * Angular attribute directive that enables components to access and respond to the current site context.
 * It provides a way for DOM elements to adapt based on the current selected site, supporting
 * the site-scoped access control model of the application.
 *
 * Usage examples:
 * - Basic site context awareness: <div appSiteContext></div>
 * - Site-specific display: <div appSiteContext [showForSiteId]="123"></div>
 * - React to site changes: <div appSiteContext (siteContextChange)="onSiteChange($event)"></div>
 */
@Directive({
  selector: '[appSiteContext]'
})
export class SiteContextDirective implements OnInit, OnDestroy {
  /**
   * Optional site ID to conditionally show/hide the element.
   * When specified, the element will only be visible when the current site matches this ID.
   */
  @Input() showForSiteId?: number;

  /**
   * Emits when the site context changes, providing the new site context information.
   * Components can subscribe to this to react to site changes.
   */
  @Output() siteContextChange: EventEmitter<SiteContext>;

  /**
   * Subscription to the site context changes, stored for cleanup on destroy.
   */
  private siteSubscription!: Subscription;

  /**
   * The current site ID, cached for performance and conditional rendering.
   */
  private currentSiteId: number | null;

  /**
   * Initializes the directive with required dependencies.
   *
   * @param el Reference to the host DOM element
   * @param renderer Angular's renderer for safe DOM manipulation
   * @param userContextService Service for accessing user's site context
   */
  constructor(
    private el: ElementRef,
    private renderer: Renderer2,
    private userContextService: UserContextService
  ) {
    this.siteContextChange = new EventEmitter<SiteContext>();
    this.currentSiteId = null;
  }

  /**
   * Lifecycle hook for initialization. Sets up the subscription to site context changes
   * and applies initial site context to the element.
   */
  ngOnInit(): void {
    // Get initial site ID
    this.currentSiteId = this.getCurrentSiteId();
    
    // Subscribe to site context changes
    this.siteSubscription = this.userContextService.currentSite$.subscribe(
      (siteContext) => {
        if (siteContext) {
          this.onSiteChange(siteContext);
        }
      }
    );
    
    // Set initial data attribute
    if (this.currentSiteId) {
      this.renderer.setAttribute(this.el.nativeElement, 'data-site-id', this.currentSiteId.toString());
    }
    
    // Initial visibility update based on showForSiteId
    this.updateElementVisibility();
  }

  /**
   * Lifecycle hook for cleanup. Unsubscribes from site context changes
   * to prevent memory leaks.
   */
  ngOnDestroy(): void {
    if (this.siteSubscription) {
      this.siteSubscription.unsubscribe();
    }
  }

  /**
   * Handles site context changes and updates the element accordingly.
   *
   * @param siteContext The new site context information
   */
  private onSiteChange(siteContext: SiteContext): void {
    // Update current site ID
    this.currentSiteId = siteContext.site_id;
    
    // Update data attribute
    this.renderer.setAttribute(this.el.nativeElement, 'data-site-id', siteContext.site_id.toString());
    
    // Update visibility based on showForSiteId
    this.updateElementVisibility();
    
    // Emit site context change event
    this.siteContextChange.emit(siteContext);
    
    // Add site-specific CSS class for styling
    const siteClass = `site-${siteContext.site_id}`;
    this.renderer.addClass(this.el.nativeElement, siteClass);
  }

  /**
   * Updates the element's visibility based on site context and showForSiteId.
   * If showForSiteId is specified, the element will only be visible when
   * the current site matches that ID.
   */
  private updateElementVisibility(): void {
    // If showForSiteId is not set, always show the element
    if (this.showForSiteId === undefined) {
      this.renderer.removeStyle(this.el.nativeElement, 'display');
      return;
    }
    
    // Show/hide based on site match
    if (this.currentSiteId === this.showForSiteId) {
      this.renderer.removeStyle(this.el.nativeElement, 'display');
    } else {
      this.renderer.setStyle(this.el.nativeElement, 'display', 'none');
    }
  }

  /**
   * Gets the current site ID from the user context.
   * 
   * @returns The current site ID or null if none selected
   */
  getCurrentSiteId(): number | null {
    return this.userContextService.getCurrentSiteId();
  }
}