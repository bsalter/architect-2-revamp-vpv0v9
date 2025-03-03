import { Injectable } from '@angular/core'; // v16.2.0
import { Observable, BehaviorSubject, of } from 'rxjs'; // v7.8.1
import { catchError, tap, map, shareReplay } from 'rxjs/operators'; // v7.8.1

import { ApiService } from '../../../core/http/api.service';
import { InteractionService } from '../../../features/interactions/services/interaction.service';
import { SiteSelectionService } from '../../../core/auth/site-selection.service';
import { CacheService } from '../../../core/cache/cache.service';
import { Interaction, InteractionDetail } from '../../interactions/models/interaction.model';

/**
 * Service responsible for retrieving and managing dashboard data with site-scoping
 * Provides methods to fetch summary statistics, recent interactions, upcoming interactions,
 * and interaction type breakdowns with appropriate caching mechanisms.
 */
@Injectable({
  providedIn: 'root'
})
export class DashboardService {
  // BehaviorSubject to track loading state
  private loading$ = new BehaviorSubject<boolean>(false);
  
  // Cache keys for different dashboard data components
  private DASHBOARD_CACHE_KEY = 'dashboard-data';
  private RECENT_INTERACTIONS_CACHE_KEY = 'recent-interactions';
  private UPCOMING_INTERACTIONS_CACHE_KEY = 'upcoming-interactions';
  private INTERACTIONS_BY_TYPE_CACHE_KEY = 'interactions-by-type';
  private INTERACTIONS_SUMMARY_CACHE_KEY = 'interactions-summary';
  
  // Cache duration in milliseconds (5 minutes)
  private CACHE_TTL = 5 * 60 * 1000;

  /**
   * Initializes the dashboard service with required dependencies
   * 
   * @param apiService Service for making API requests
   * @param interactionService Service for accessing interaction data
   * @param siteService Service for site context management
   * @param cacheService Service for caching dashboard data
   */
  constructor(
    private apiService: ApiService,
    private interactionService: InteractionService,
    private siteService: SiteSelectionService,
    private cacheService: CacheService
  ) {}
  
  /**
   * Retrieves comprehensive dashboard data for the current site
   * 
   * @param useCache Whether to use cached data if available
   * @returns Observable with complete dashboard data
   */
  getDashboardData(useCache: boolean = true): Observable<any> {
    this.loading$.next(true);
    
    const siteId = this.siteService.getCurrentSiteId();
    if (!siteId) {
      this.loading$.next(false);
      return of({ error: 'No site selected' });
    }
    
    const cacheKey = this.generateCacheKey(this.DASHBOARD_CACHE_KEY, siteId);
    
    // Check cache first if enabled
    if (useCache) {
      const cachedData = this.cacheService.get(cacheKey);
      if (cachedData) {
        this.loading$.next(false);
        return of(cachedData);
      }
    }
    
    // If not cached or cache disabled, fetch from API
    return this.apiService.get<any>('/api/dashboard', null, useCache).pipe(
      tap(data => {
        if (useCache) {
          this.cacheService.set(cacheKey, data, this.CACHE_TTL);
        }
      }),
      catchError(error => {
        console.error('Error fetching dashboard data:', error);
        return of({ error: true });
      }),
      tap(() => this.loading$.next(false))
    );
  }
  
  /**
   * Retrieves the most recent interactions for the current site
   * 
   * @param limit Maximum number of interactions to return
   * @param useCache Whether to use cached data if available
   * @returns Observable with recent interactions
   */
  getRecentInteractions(limit: number = 5, useCache: boolean = true): Observable<Interaction[]> {
    this.loading$.next(true);
    
    const siteId = this.siteService.getCurrentSiteId();
    if (!siteId) {
      this.loading$.next(false);
      return of([]);
    }
    
    const cacheKey = this.generateCacheKey(`${this.RECENT_INTERACTIONS_CACHE_KEY}-${limit}`, siteId);
    
    // Check cache first if enabled
    if (useCache) {
      const cachedData = this.cacheService.get(cacheKey);
      if (cachedData) {
        this.loading$.next(false);
        return of(cachedData);
      }
    }
    
    // If not cached or cache disabled, fetch from API
    return this.apiService.get<{ interactions: Interaction[] }>('/api/dashboard/recent', { 
      limit 
    }, useCache).pipe(
      map(response => response.interactions || []),
      tap(data => {
        if (useCache) {
          this.cacheService.set(cacheKey, data, this.CACHE_TTL);
        }
      }),
      catchError(error => {
        console.error('Error fetching recent interactions:', error);
        return of([]);
      }),
      tap(() => this.loading$.next(false))
    );
  }
  
  /**
   * Retrieves upcoming interactions within a specified timeframe
   * 
   * @param days Number of days in the future to include
   * @param limit Maximum number of interactions to return
   * @param useCache Whether to use cached data if available
   * @returns Observable with upcoming interactions
   */
  getUpcomingInteractions(days: number = 7, limit: number = 5, useCache: boolean = true): Observable<Interaction[]> {
    this.loading$.next(true);
    
    const siteId = this.siteService.getCurrentSiteId();
    if (!siteId) {
      this.loading$.next(false);
      return of([]);
    }
    
    const cacheKey = this.generateCacheKey(`${this.UPCOMING_INTERACTIONS_CACHE_KEY}-${days}-${limit}`, siteId);
    
    // Check cache first if enabled
    if (useCache) {
      const cachedData = this.cacheService.get(cacheKey);
      if (cachedData) {
        this.loading$.next(false);
        return of(cachedData);
      }
    }
    
    // If not cached or cache disabled, fetch from API
    return this.apiService.get<{ interactions: Interaction[] }>('/api/dashboard/upcoming', { 
      days,
      limit 
    }, useCache).pipe(
      map(response => response.interactions || []),
      tap(data => {
        if (useCache) {
          this.cacheService.set(cacheKey, data, this.CACHE_TTL);
        }
      }),
      catchError(error => {
        console.error('Error fetching upcoming interactions:', error);
        return of([]);
      }),
      tap(() => this.loading$.next(false))
    );
  }
  
  /**
   * Retrieves a breakdown of interactions by type for charting
   * 
   * @param useCache Whether to use cached data if available
   * @returns Observable with interaction counts by type
   */
  getInteractionsByType(useCache: boolean = true): Observable<any[]> {
    this.loading$.next(true);
    
    const siteId = this.siteService.getCurrentSiteId();
    if (!siteId) {
      this.loading$.next(false);
      return of([]);
    }
    
    const cacheKey = this.generateCacheKey(this.INTERACTIONS_BY_TYPE_CACHE_KEY, siteId);
    
    // Check cache first if enabled
    if (useCache) {
      const cachedData = this.cacheService.get(cacheKey);
      if (cachedData) {
        this.loading$.next(false);
        return of(cachedData);
      }
    }
    
    // If not cached or cache disabled, fetch from API
    return this.apiService.get<any[]>('/api/dashboard/by-type', null, useCache).pipe(
      tap(data => {
        if (useCache) {
          this.cacheService.set(cacheKey, data, this.CACHE_TTL);
        }
      }),
      catchError(error => {
        console.error('Error fetching interactions by type:', error);
        return of([]);
      }),
      tap(() => this.loading$.next(false))
    );
  }
  
  /**
   * Retrieves summary statistics for interactions
   * 
   * @param useCache Whether to use cached data if available
   * @returns Observable with summary statistics
   */
  getInteractionsSummary(useCache: boolean = true): Observable<any> {
    this.loading$.next(true);
    
    const siteId = this.siteService.getCurrentSiteId();
    if (!siteId) {
      this.loading$.next(false);
      return of({});
    }
    
    const cacheKey = this.generateCacheKey(this.INTERACTIONS_SUMMARY_CACHE_KEY, siteId);
    
    // Check cache first if enabled
    if (useCache) {
      const cachedData = this.cacheService.get(cacheKey);
      if (cachedData) {
        this.loading$.next(false);
        return of(cachedData);
      }
    }
    
    // If not cached or cache disabled, fetch from API
    return this.apiService.get<any>('/api/dashboard/summary', null, useCache).pipe(
      tap(data => {
        if (useCache) {
          this.cacheService.set(cacheKey, data, this.CACHE_TTL);
        }
      }),
      catchError(error => {
        console.error('Error fetching interactions summary:', error);
        return of({});
      }),
      tap(() => this.loading$.next(false))
    );
  }
  
  /**
   * Clears all dashboard-related caches to force fresh data
   */
  refreshDashboard(): void {
    const siteId = this.siteService.getCurrentSiteId();
    if (!siteId) return;
    
    // Clear all dashboard-related caches
    this.cacheService.remove(this.generateCacheKey(this.DASHBOARD_CACHE_KEY, siteId));
    this.cacheService.remove(this.generateCacheKey(this.RECENT_INTERACTIONS_CACHE_KEY, siteId));
    this.cacheService.remove(this.generateCacheKey(this.UPCOMING_INTERACTIONS_CACHE_KEY, siteId));
    this.cacheService.remove(this.generateCacheKey(this.INTERACTIONS_BY_TYPE_CACHE_KEY, siteId));
    this.cacheService.remove(this.generateCacheKey(this.INTERACTIONS_SUMMARY_CACHE_KEY, siteId));
    
    // Invalidate API cache for dashboard endpoints
    this.apiService.invalidateCache('/api/dashboard', true);
  }
  
  /**
   * Checks if dashboard data is currently loading
   * 
   * @returns Observable of loading state
   */
  isLoading(): Observable<boolean> {
    return this.loading$.asObservable();
  }
  
  /**
   * Generates a cache key for dashboard data scoped to site
   * 
   * @param baseKey Base cache key
   * @param siteId Site ID for scoping
   * @returns Cache key string
   */
  private generateCacheKey(baseKey: string, siteId: number): string {
    return `${baseKey}-site-${siteId}`;
  }
}