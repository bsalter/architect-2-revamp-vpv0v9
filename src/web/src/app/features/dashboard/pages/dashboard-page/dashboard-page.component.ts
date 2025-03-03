import { Component, OnInit, OnDestroy } from '@angular/core'; // v16.2.0
import { Router } from '@angular/router'; // v16.2.0
import { Subscription, Observable, Subject } from 'rxjs'; // v7.8.1
import { takeUntil, filter } from 'rxjs/operators'; // v7.8.1

import { DashboardService } from '../../services/dashboard.service';
import { UserContextService } from '../../../../core/auth/user-context.service';
import { BreadcrumbService } from '../../../../shared/services/breadcrumb.service';
import { Interaction } from '../../../interactions/models/interaction.model';
import { SiteWithRole } from '../../../sites/models/site.model';

/**
 * Component that displays the main dashboard page with site-scoped interaction data and metrics.
 * Provides an overview of recent and upcoming interactions along with summary statistics
 * for the current site context.
 */
@Component({
  selector: 'app-dashboard-page',
  templateUrl: './dashboard-page.component.html',
  styleUrls: ['./dashboard-page.component.scss']
})
export class DashboardPageComponent implements OnInit, OnDestroy {
  // Recent and upcoming interactions
  recentInteractions: Interaction[] = [];
  upcomingInteractions: Interaction[] = [];
  
  // Summary statistics and interaction type distribution
  summaryData: any;
  interactionsByType: any[] = [];
  
  // UI state
  loading = false;
  currentSite: SiteWithRole | null = null;
  canCreateInteraction = false;
  
  // Subject for managing subscriptions
  private destroy$ = new Subject<void>();

  /**
   * Initializes the dashboard page component with required dependencies
   * 
   * @param dashboardService Service for accessing dashboard data
   * @param userContextService Service for user authentication and permission context
   * @param breadcrumbService Service for managing breadcrumb navigation
   * @param router Angular router for navigation
   */
  constructor(
    private dashboardService: DashboardService,
    private userContextService: UserContextService,
    private breadcrumbService: BreadcrumbService,
    private router: Router
  ) {}

  /**
   * Lifecycle hook that initializes the component
   * Sets up subscriptions and loads dashboard data
   */
  ngOnInit(): void {
    // Set up breadcrumbs for dashboard page
    this.breadcrumbService.setBreadcrumbs([
      { label: 'Dashboard', url: '/dashboard' }
    ]);
    
    // Subscribe to loading state
    this.dashboardService.isLoading()
      .pipe(takeUntil(this.destroy$))
      .subscribe(loading => {
        this.loading = loading;
      });
    
    // Subscribe to current site changes
    this.userContextService.currentSite$
      .pipe(
        takeUntil(this.destroy$),
        filter(site => site !== null)
      )
      .subscribe(site => {
        this.currentSite = site;
        this.loadDashboardData();
      });
    
    // Check if user has permission to create interactions
    this.canCreateInteraction = this.userContextService.isEditor();
  }

  /**
   * Lifecycle hook that cleans up subscriptions when component is destroyed
   */
  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * Loads all dashboard data from the service
   */
  loadDashboardData(): void {
    // Get recent interactions (last 5)
    this.dashboardService.getRecentInteractions(5)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (interactions) => {
          this.recentInteractions = interactions;
        },
        error: (error) => {
          console.error('Error loading recent interactions:', error);
        }
      });
    
    // Get upcoming interactions (next 7 days, limit 5)
    this.dashboardService.getUpcomingInteractions(7, 5)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (interactions) => {
          this.upcomingInteractions = interactions;
        },
        error: (error) => {
          console.error('Error loading upcoming interactions:', error);
        }
      });
    
    // Get interaction distribution by type
    this.dashboardService.getInteractionsByType()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => {
          this.interactionsByType = data;
        },
        error: (error) => {
          console.error('Error loading interactions by type:', error);
        }
      });
    
    // Get summary statistics
    this.dashboardService.getInteractionsSummary()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => {
          this.summaryData = data;
        },
        error: (error) => {
          console.error('Error loading interactions summary:', error);
        }
      });
  }

  /**
   * Refreshes all dashboard data by clearing cache and reloading
   */
  refreshDashboard(): void {
    this.dashboardService.refreshDashboard();
    this.loadDashboardData();
  }

  /**
   * Navigates to a specific interaction detail page
   * 
   * @param interactionId The ID of the interaction to navigate to
   */
  navigateToInteraction(interactionId: number): void {
    this.router.navigate(['/interactions', interactionId]);
  }

  /**
   * Navigates to the interaction creation page
   */
  navigateToCreate(): void {
    this.router.navigate(['/interactions/create']);
  }

  /**
   * Navigates to the interaction finder page
   */
  navigateToFinder(): void {
    this.router.navigate(['/interactions']);
  }
}