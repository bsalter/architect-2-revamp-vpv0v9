import { Injectable } from '@angular/core'; // v16.2.0
import { Router, NavigationEnd } from '@angular/router'; // v16.2.0
import { filter, takeUntil, debounceTime, skip } from 'rxjs/operators'; // v7.8.1
import { Subject } from 'rxjs'; // v7.8.1

import { ApiService } from '../http/api.service';
import { UserContextService } from '../auth/user-context.service';
import { AppConfigService } from '../config/app-config.service';
import { formatDate } from '../utils/datetime-utils';
import { environment } from '../../../environments/environment';

// Maximum number of activities to store in buffer before sending to backend
const ACTIVITY_BUFFER_SIZE = 50;

// Interval for sending activities to backend (1 minute)
const FLUSH_INTERVAL_MS = 60000;

/**
 * Enum defining various types of user activities that can be tracked
 */
export enum ActivityType {
  PAGE_VIEW = 'page_view',
  INTERACTION_CREATE = 'interaction_create',
  INTERACTION_UPDATE = 'interaction_update',
  INTERACTION_DELETE = 'interaction_delete',
  SEARCH_EXECUTE = 'search_execute',
  FILTER_APPLY = 'filter_apply',
  SITE_SWITCH = 'site_switch',
  LOGIN = 'login',
  LOGOUT = 'logout',
  FEATURE_USE = 'feature_use'
}

/**
 * Interface defining the structure of a user activity event
 */
export interface UserActivity {
  type: string;
  userId: string;
  siteId: number;
  url: string;
  timestamp: Date;
  details: Record<string, any>;
  sessionId: string;
}

/**
 * Service responsible for tracking and logging user activities within the Interaction Management System.
 * This service captures user interactions such as page views, feature usage, search operations, and
 * CRUD actions on interactions to provide insights into user behavior patterns and application usage statistics.
 */
@Injectable({
  providedIn: 'root'
})
export class UserActivityService {
  private enabled: boolean = false;
  private activityBuffer: Array<UserActivity> = [];
  private sessionId: string = '';
  private currentPageUrl: string = '';
  private flushInterval: number = FLUSH_INTERVAL_MS;
  private flushTimer: any;
  private destroy$ = new Subject<void>();

  constructor(
    private router: Router,
    private apiService: ApiService,
    private userContext: UserContextService,
    private configService: AppConfigService
  ) {
    this.initialize();
  }

  /**
   * Initialize the activity tracking service with configuration
   */
  private initialize(): void {
    // Get logging configuration from AppConfigService
    const loggingConfig = this.configService.getLoggingConfig();
    
    // Enable tracking based on configuration
    this.enabled = loggingConfig?.enableConsoleLogging ?? environment.logging?.enableConsoleLogging ?? false;
    
    // Generate a unique session ID for this browser session
    this.sessionId = this.generateSessionId();
    
    // Initialize activity buffer
    this.activityBuffer = [];
    
    // Set up router subscription for page view tracking
    this.router.events.pipe(
      filter(event => event instanceof NavigationEnd),
      takeUntil(this.destroy$)
    ).subscribe((event: NavigationEnd) => {
      this.trackPageView(event.urlAfterRedirects);
    });
    
    // Set up user context subscription for login/logout events
    this.userContext.currentUser$.pipe(
      skip(1), // Skip initial emission
      takeUntil(this.destroy$)
    ).subscribe(user => {
      if (user) {
        // User logged in or changed
        this.trackActivity(ActivityType.LOGIN, {
          method: 'token', // Assuming token-based login
          timestamp: new Date().toISOString()
        });
      } else {
        // User logged out
        this.trackActivity(ActivityType.LOGOUT, {
          timestamp: new Date().toISOString()
        });
      }
    });
    
    // Set up periodic flushing of activity buffer
    if (this.enabled) {
      this.flushTimer = setInterval(() => {
        this.flushActivities();
      }, this.flushInterval);
    }
  }

  /**
   * Log a user activity event
   * @param type The type of activity
   * @param details Additional details about the activity
   */
  trackActivity(type: string, details: Record<string, any> = {}): void {
    if (!this.enabled) return;
    
    const user = this.userContext.getCurrentUser();
    const siteId = this.userContext.getCurrentSiteId() || 0;
    
    if (!user) return; // Don't track activities for unauthenticated users
    
    const activity: UserActivity = {
      type,
      userId: user.id,
      siteId,
      url: this.currentPageUrl || window.location.href,
      timestamp: new Date(),
      details,
      sessionId: this.sessionId
    };
    
    // Add to buffer
    this.activityBuffer.push(activity);
    
    // If buffer exceeds maximum size, remove oldest entries
    while (this.activityBuffer.length > ACTIVITY_BUFFER_SIZE) {
      this.activityBuffer.shift();
    }
    
    // Log activity in development mode
    if (!this.configService.isProduction()) {
      console.debug('Activity tracked:', activity);
    }
  }

  /**
   * Track page view when navigation completes
   * @param url The page URL being viewed
   */
  trackPageView(url: string): void {
    this.currentPageUrl = url;
    
    // Extract route path from URL
    const urlObj = new URL(url, window.location.origin);
    const path = urlObj.pathname;
    
    this.trackActivity(ActivityType.PAGE_VIEW, {
      path,
      url,
      timestamp: formatDate(new Date(), 'yyyy-MM-dd HH:mm:ss')
    });
  }

  /**
   * Track creation of a new interaction
   * @param interaction The interaction data that was created
   */
  trackInteractionCreate(interaction: any): void {
    this.trackActivity(ActivityType.INTERACTION_CREATE, {
      interactionId: interaction.id,
      title: interaction.title,
      type: interaction.type,
      timestamp: formatDate(new Date(), 'yyyy-MM-dd HH:mm:ss')
    });
  }

  /**
   * Track update of an existing interaction
   * @param interaction The updated interaction data
   * @param changedFields Array of field names that were changed
   */
  trackInteractionUpdate(interaction: any, changedFields: string[] = []): void {
    this.trackActivity(ActivityType.INTERACTION_UPDATE, {
      interactionId: interaction.id,
      changedFields,
      timestamp: formatDate(new Date(), 'yyyy-MM-dd HH:mm:ss')
    });
  }

  /**
   * Track deletion of an interaction
   * @param interactionId ID of the deleted interaction
   */
  trackInteractionDelete(interactionId: number): void {
    this.trackActivity(ActivityType.INTERACTION_DELETE, {
      interactionId,
      timestamp: formatDate(new Date(), 'yyyy-MM-dd HH:mm:ss')
    });
  }

  /**
   * Track search operation execution
   * @param searchTerm The search term entered by the user
   * @param filters Any filters applied with the search
   * @param resultCount Number of results returned
   */
  trackSearch(searchTerm: string, filters: object = {}, resultCount: number = 0): void {
    this.trackActivity(ActivityType.SEARCH_EXECUTE, {
      searchTerm,
      filters,
      resultCount,
      timestamp: formatDate(new Date(), 'yyyy-MM-dd HH:mm:ss')
    });
  }

  /**
   * Track when filters are applied in the finder view
   * @param filters The filter criteria applied
   */
  trackFilterApply(filters: object): void {
    this.trackActivity(ActivityType.FILTER_APPLY, {
      filters,
      timestamp: formatDate(new Date(), 'yyyy-MM-dd HH:mm:ss')
    });
  }

  /**
   * Track when user switches between sites
   * @param previousSiteId The previous site ID
   * @param newSiteId The new site ID
   */
  trackSiteSwitch(previousSiteId: number, newSiteId: number): void {
    this.trackActivity(ActivityType.SITE_SWITCH, {
      previousSiteId,
      newSiteId,
      timestamp: formatDate(new Date(), 'yyyy-MM-dd HH:mm:ss')
    });
  }

  /**
   * Track usage of specific application features
   * @param featureName Name of the feature being used
   * @param featureDetails Additional details about feature usage
   */
  trackFeatureUse(featureName: string, featureDetails: Record<string, any> = {}): void {
    this.trackActivity(ActivityType.FEATURE_USE, {
      feature: featureName,
      ...featureDetails,
      timestamp: formatDate(new Date(), 'yyyy-MM-dd HH:mm:ss')
    });
  }

  /**
   * Send collected activities to the backend for storage
   * @returns Promise resolving to success status
   */
  flushActivities(): Promise<boolean> {
    if (this.activityBuffer.length === 0) {
      return Promise.resolve(true);
    }
    
    // Create a copy of the current buffer
    const activities = [...this.activityBuffer];
    
    // Clear the buffer before sending to avoid duplicates
    this.activityBuffer = [];
    
    // Format payload with activities and metadata
    const payload = {
      activities,
      timestamp: new Date(),
      sessionId: this.sessionId,
      userAgent: navigator.userAgent
    };
    
    return new Promise((resolve) => {
      this.apiService.post('/api/activity/log', payload).subscribe({
        next: () => {
          // Log success in development mode
          if (!this.configService.isProduction()) {
            console.debug(`Sent ${activities.length} activities to backend`);
          }
          resolve(true);
        },
        error: (error) => {
          // Put activities back in buffer for next attempt
          this.activityBuffer = [...activities, ...this.activityBuffer];
          
          // Log error in development mode
          if (!this.configService.isProduction()) {
            console.error('Failed to send activities to backend:', error);
          }
          resolve(false);
        }
      });
    });
  }

  /**
   * Get the current session identifier
   * @returns Current session ID
   */
  getSessionId(): string {
    return this.sessionId;
  }

  /**
   * Generate a unique session identifier
   * @returns New session ID
   */
  private generateSessionId(): string {
    const timestamp = new Date().getTime();
    const random = Math.random().toString(36).substring(2, 10);
    return `${timestamp}-${random}`;
  }

  /**
   * Check if activity tracking is enabled
   * @returns True if tracking is enabled
   */
  isEnabled(): boolean {
    return this.enabled;
  }

  /**
   * Enable or disable activity tracking
   * @param state True to enable, false to disable
   */
  setEnabled(state: boolean): void {
    this.enabled = state;
    
    if (state && !this.flushTimer) {
      // Start flush timer if enabling
      this.flushTimer = setInterval(() => {
        this.flushActivities();
      }, this.flushInterval);
    } else if (!state && this.flushTimer) {
      // Clear timer if disabling
      clearInterval(this.flushTimer);
      this.flushTimer = null;
    }
    
    // Log state change in development mode
    if (!this.configService.isProduction()) {
      console.log(`User activity tracking ${state ? 'enabled' : 'disabled'}`);
    }
  }

  /**
   * Lifecycle hook for service cleanup
   */
  ngOnDestroy(): void {
    // Complete the destroy subject to unsubscribe from observables
    this.destroy$.next();
    this.destroy$.complete();
    
    // Clear flush timer
    if (this.flushTimer) {
      clearInterval(this.flushTimer);
      this.flushTimer = null;
    }
    
    // Flush any remaining activities
    this.flushActivities();
  }
}