import { Injectable } from '@angular/core'; // v16.2.0
import { Observable, of, BehaviorSubject } from 'rxjs'; // v7.8.1
import { map, catchError, tap, finalize } from 'rxjs/operators'; // v7.8.1

import { ApiService } from '../../../core/http/api.service';
import { Interaction, InteractionCreate, InteractionUpdate, InteractionResponse, InteractionListResponse } from '../models/interaction.model';
import { CacheService } from '../../../core/cache/cache.service';
import { SiteSelectionService } from '../../../core/auth/site-selection.service';

/**
 * Service that provides CRUD operations for Interaction entities, communicating
 * with the backend API, managing state, and implementing caching mechanisms for
 * improved performance. Implements site-scoped access control for interactions.
 */
@Injectable({
  providedIn: 'root'
})
export class InteractionService {
  private readonly API_ENDPOINT = 'interactions';
  
  // BehaviorSubjects for state management
  private loadingSubject = new BehaviorSubject<boolean>(false);
  public loading$ = this.loadingSubject.asObservable();
  
  private errorSubject = new BehaviorSubject<any>(null);
  public error$ = this.errorSubject.asObservable();

  /**
   * Initializes the interaction service with required dependencies
   * 
   * @param apiService Service for making API requests
   * @param cacheService Service for caching interaction data
   * @param siteService Service for getting current site context
   */
  constructor(
    private apiService: ApiService,
    private cacheService: CacheService,
    private siteService: SiteSelectionService
  ) {
    // Initialize behavior subjects
    this.loadingSubject = new BehaviorSubject<boolean>(false);
    this.loading$ = this.loadingSubject.asObservable();
    
    this.errorSubject = new BehaviorSubject<any>(null);
    this.error$ = this.errorSubject.asObservable();
  }

  /**
   * Retrieves a paginated list of interactions for the current site
   * 
   * @param page Page number (default: 1)
   * @param pageSize Items per page (default: 10) 
   * @param useCache Whether to use cache (default: true)
   * @returns Observable stream of interaction list response
   */
  getInteractions(page: number = 1, pageSize: number = 10, useCache: boolean = true): Observable<InteractionListResponse> {
    this.loadingSubject.next(true);
    this.errorSubject.next(null);
    
    const params = {
      page,
      page_size: pageSize
    };
    
    // Site ID is automatically added by the ApiService
    return this.apiService.get<InteractionListResponse>(
      this.API_ENDPOINT,
      params,
      useCache
    ).pipe(
      catchError(error => this.handleError(error)),
      finalize(() => this.loadingSubject.next(false))
    );
  }

  /**
   * Retrieves a single interaction by ID
   * 
   * @param id Interaction ID
   * @param useCache Whether to use cache (default: true)
   * @returns Observable of the requested interaction
   */
  getInteraction(id: number, useCache: boolean = true): Observable<Interaction> {
    this.loadingSubject.next(true);
    this.errorSubject.next(null);
    
    // Check cache first if enabled
    if (useCache) {
      const cachedInteraction = this.cacheService.getInteraction(id);
      if (cachedInteraction) {
        this.loadingSubject.next(false);
        return of(cachedInteraction);
      }
    }
    
    return this.apiService.get<InteractionResponse>(
      `${this.API_ENDPOINT}/${id}`,
      null,
      useCache
    ).pipe(
      map(response => response.interaction),
      tap(interaction => {
        // Cache the interaction for future requests
        if (useCache && interaction) {
          this.cacheService.setInteraction(id, interaction);
        }
      }),
      catchError(error => this.handleError(error)),
      finalize(() => this.loadingSubject.next(false))
    );
  }

  /**
   * Creates a new interaction
   * 
   * @param interaction Interaction data to create
   * @returns Observable of the created interaction
   */
  createInteraction(interaction: InteractionCreate): Observable<Interaction> {
    this.loadingSubject.next(true);
    this.errorSubject.next(null);
    
    // Ensure interaction has the current site ID
    const currentSiteId = this.siteService.getCurrentSiteId();
    if (currentSiteId && !interaction.siteId) {
      interaction.siteId = currentSiteId;
    }
    
    return this.apiService.post<InteractionResponse>(
      this.API_ENDPOINT,
      interaction
    ).pipe(
      map(response => response.interaction),
      tap(() => {
        // Invalidate caches after creating a new interaction
        this.invalidateInteractionCache();
      }),
      catchError(error => this.handleError(error)),
      finalize(() => this.loadingSubject.next(false))
    );
  }

  /**
   * Updates an existing interaction
   * 
   * @param id Interaction ID to update
   * @param interaction Updated interaction data
   * @returns Observable of the updated interaction
   */
  updateInteraction(id: number, interaction: InteractionUpdate): Observable<Interaction> {
    this.loadingSubject.next(true);
    this.errorSubject.next(null);
    
    return this.apiService.put<InteractionResponse>(
      `${this.API_ENDPOINT}/${id}`,
      interaction
    ).pipe(
      map(response => response.interaction),
      tap(() => {
        // Invalidate specific interaction cache and list cache
        this.invalidateInteractionCache(id);
      }),
      catchError(error => this.handleError(error)),
      finalize(() => this.loadingSubject.next(false))
    );
  }

  /**
   * Deletes an interaction by ID
   * 
   * @param id Interaction ID to delete
   * @returns Observable indicating success
   */
  deleteInteraction(id: number): Observable<boolean> {
    this.loadingSubject.next(true);
    this.errorSubject.next(null);
    
    return this.apiService.delete<any>(
      `${this.API_ENDPOINT}/${id}`
    ).pipe(
      map(() => true),
      tap(() => {
        // Invalidate specific interaction cache and list cache
        this.invalidateInteractionCache(id);
      }),
      catchError(error => this.handleError(error)),
      finalize(() => this.loadingSubject.next(false))
    );
  }

  /**
   * Invalidates interaction caches
   * 
   * @param id Optional specific interaction ID to invalidate
   */
  invalidateInteractionCache(id: number = null): void {
    if (id) {
      // Invalidate specific interaction cache
      this.cacheService.remove(`interaction-${id}`);
    }
    
    // Invalidate interaction list cache
    this.cacheService.invalidateInteractionCache();
    
    // Invalidate search results cache via apiService
    this.apiService.invalidateCache('search', true);
  }

  /**
   * Handles and processes API errors
   * 
   * @param error Error object
   * @returns Observable that errors
   */
  private handleError(error: any): Observable<never> {
    // Set error state by updating errorSubject with error details
    this.errorSubject.next(error);
    
    // Log error to console
    console.error('Interaction service error:', error);
    
    // Format user-friendly error message
    const errorMessage = error.message || 'An unexpected error occurred';
    
    // Return error Observable
    return throwError(() => error);
  }
}