import { Directive, Input, OnInit, OnDestroy, TemplateRef, ViewContainerRef } from '@angular/core'; // v16.2.0
import { Subscription } from 'rxjs'; // v7.8.1

import { UserContextService } from '../../core/auth/user-context.service';
import { UserRoleEnum } from '../../core/auth/user.model';

/**
 * Directive that conditionally shows or hides DOM elements based on user role permissions.
 * Supports site-scoped authorization by checking if the current user has the required
 * permission for a specific site.
 * 
 * Usage:
 * <div *appHasPermission="'admin'" [siteId]="siteId">
 *   Content only visible to admins
 * </div>
 * 
 * <div *appHasPermission="'editor'" [invert]="true">
 *   Content visible to everyone except editors and admins
 * </div>
 * 
 * <button *appHasPermission="UserRoleEnum.SITE_ADMIN">Admin Only Action</button>
 */
@Directive({
  selector: '[appHasPermission]'
})
export class HasPermissionDirective implements OnInit, OnDestroy {
  /**
   * The required role or permission level.
   * Can be a role enum value or shorthand strings: 'admin', 'editor', 'viewer'
   */
  @Input('appHasPermission') requiredRole!: string;
  
  /**
   * Optional site ID to check permissions against.
   * If not provided, the current site context will be used.
   */
  @Input() siteId: number | null = null;
  
  /**
   * Whether to invert the permission logic.
   * If true, content is shown when user does NOT have permission.
   * If false (default), content is shown when user has permission.
   */
  @Input() invert = false;
  
  /**
   * Subscription to user context changes
   */
  private permissionSubscription: Subscription = new Subscription();

  /**
   * Initializes the directive with required dependencies
   * 
   * @param templateRef Reference to the template content
   * @param viewContainer Container where template will be rendered
   * @param userContextService Service for checking user permissions
   */
  constructor(
    private templateRef: TemplateRef<any>,
    private viewContainer: ViewContainerRef,
    private userContextService: UserContextService
  ) {}

  /**
   * Initializes directive and subscribes to relevant changes
   */
  ngOnInit(): void {
    // Subscribe to user context changes to update visibility when permissions change
    this.permissionSubscription = this.userContextService.currentUser$.subscribe(() => {
      this.updateView();
    });

    // Initial update
    this.updateView();
  }

  /**
   * Clean up subscriptions when directive is destroyed
   */
  ngOnDestroy(): void {
    // Unsubscribe from permission change subscriptions to prevent memory leaks
    if (this.permissionSubscription) {
      this.permissionSubscription.unsubscribe();
    }
  }

  /**
   * Updates the element visibility based on permission checks
   */
  private updateView(): void {
    // Clear the view container to remove previous content
    this.viewContainer.clear();

    // Check if user has required permission
    const hasPermission = this.checkPermission();

    // If invert is false, show content when user has permission
    // If invert is true, show content when user does not have permission
    if ((!this.invert && hasPermission) || (this.invert && !hasPermission)) {
      this.viewContainer.createEmbeddedView(this.templateRef);
    }
  }

  /**
   * Evaluates if user has the required permission for the specified site
   * 
   * @returns Whether user has the required permission
   */
  private checkPermission(): boolean {
    // Handle special shorthand permission cases
    if (this.requiredRole === 'admin') {
      return this.userContextService.isAdmin(this.siteId);
    } else if (this.requiredRole === 'editor') {
      return this.userContextService.isEditor(this.siteId);
    } else if (this.requiredRole === 'viewer') {
      return this.userContextService.isViewer(this.siteId);
    }

    // For specific roles, use the hasPermission method
    return this.userContextService.hasPermission(this.requiredRole, this.siteId);
  }
}