import { Injectable } from '@angular/core'; // v16.2.0
import { Observable, BehaviorSubject, of } from 'rxjs'; // v7.8.1
import { catchError, tap, map, finalize, debounceTime, distinctUntilChanged } from 'rxjs/operators'; // v7.8.1

import {
  SearchResults,
  SearchResultsResponse,
  SearchResultItem,
  EmptySearchResults
} from '../models/search-results.model';
import { SearchQuery, Filter } from '../models/filter.model';
import { Interaction } from '../models/interaction.model';
import { ApiService } from '../../../core/http/api.service';
import { SiteSelectionService } from '../../../core/auth/site-selection.service';
import { CacheService } from '../../../core/cache/cache.service';

/**
 * Service that provides comprehensive search functionality for interactions,
 * including basic and advanced filtering, pagination, and caching of search results.
 * This service is the core search engine for the Interaction Finder component.
 */
@Injectable({ providedIn: 'root' })
export class SearchService {
  // Observable streams for search results, loading state, and errors
  private searchResultsSubject = new BehaviorSubject<SearchResults>(EmptySearchResults);
  public searchResults$ = this.searchResultsSubject.asObservable();
  
  private loadingSubject = new BehaviorSubject<boolean>(false);
  public loading$ = this.loadingSubject.asObservable();
  
  private errorSubject = new BehaviorSubject<string>('');
  public error$ = this.errorSubject.asObservable();
  
  // API endpoints for search operations
  private searchEndpoint = '/api/search/interactions';
  private advancedSearchEndpoint = '/api/search/advanced';
  
  // Default pagination size
  private defaultPageSize = 10;

  /**
   * Creates an instance of SearchService
   * 
   * @param apiService Service for making HTTP requests to the backend API
   * @param siteService Service for retrieving current site context for search scoping
   * @param cacheService Service for caching search results to improve performance
   */
  constructor(
    private apiService: ApiService,
    private siteService: SiteSelectionService,
    private cacheService: CacheService
  ) {}

  /**
   * Performs a basic search for interactions with a text query and pagination
   * 
   * @param searchText The text to search for across all fields
   * @param page The page number to retrieve (1-based)
   * @param pageSize The number of items per page
   * @returns Observable with search results
   */
  search(searchText: string, page = 1, pageSize = this.defaultPageSize): Observable<SearchResults> {
    this.loadingSubject.next(true);
    this.errorSubject.next('');
    
    const siteId = this.siteService.getCurrentSiteId();
    if (!siteId) {
      return this.handleSearchError(new Error('No site selected'));
    }
    
    // Validate and prepare search parameters
    const searchQuery: SearchQuery = {
      globalSearch: searchText || '',
      page,
      pageSize: pageSize || this.defaultPageSize
    };
    
    // Check cache for existing results
    const cachedResults = this.cacheService.getSearchResults(
      siteId, 
      searchText || '', 
      page, 
      pageSize
    );
    
    if (cachedResults) {
      this.searchResultsSubject.next(cachedResults);
      this.loadingSubject.next(false);
      return of(cachedResults);
    }
    
    // Execute the search if no cache hit
    return this.executeSearch(searchQuery);
  }

  /**
   * Performs an advanced search using multiple filters, sorting, and pagination
   * 
   * @param query The search query containing filters and pagination
   * @returns Observable with search results
   */
  advancedSearch(query: SearchQuery): Observable<SearchResults> {
    this.loadingSubject.next(true);
    this.errorSubject.next('');
    
    const siteId = this.siteService.getCurrentSiteId();
    if (!siteId) {
      return this.handleSearchError(new Error('No site selected'));
    }
    
    // Validate the search query object
    const searchQuery: SearchQuery = {
      ...query,
      page: query.page || 1,
      pageSize: query.pageSize || this.defaultPageSize
    };
    
    // Create a cache key from the query
    const queryString = JSON.stringify(searchQuery);
    
    // Check cache for existing results
    const cachedResults = this.cacheService.getSearchResults(
      siteId,
      queryString,
      searchQuery.page,
      searchQuery.pageSize
    );
    
    if (cachedResults) {
      this.searchResultsSubject.next(cachedResults);
      this.loadingSubject.next(false);
      return of(cachedResults);
    }
    
    // Execute the search if no cache hit
    return this.executeSearch(searchQuery);
  }

  /**
   * Core method that executes the search API request with properly formatted parameters
   * 
   * @param query The search query to execute
   * @returns Observable with search results
   */
  private executeSearch(query: SearchQuery): Observable<SearchResults> {
    const siteId = this.siteService.getCurrentSiteId();
    
    // Determine if basic or advanced search is needed
    const isAdvancedSearch = !!query.filters && query.filters.length > 0;
    let searchObservable: Observable<SearchResultsResponse>;
    
    if (isAdvancedSearch) {
      // Use POST for advanced search with query in body
      searchObservable = this.apiService.post<SearchResultsResponse>(
        this.advancedSearchEndpoint,
        query
      );
    } else {
      // Use GET with query parameters for basic search
      const params = {
        search: query.globalSearch,
        page: query.page.toString(),
        pageSize: query.pageSize.toString()
        // site_id is automatically added by the ApiService
      };
      
      searchObservable = this.apiService.get<SearchResultsResponse>(
        this.searchEndpoint,
        params
      );
    }
    
    return searchObservable.pipe(
      map(response => this.mapResponseToSearchResults(response, query)),
      tap(results => {
        // Update the searchResultsSubject with new results
        this.searchResultsSubject.next(results);
        
        // Cache successful results for future queries
        if (siteId) {
          const queryString = isAdvancedSearch 
            ? JSON.stringify(query) 
            : (query.globalSearch || '');
            
          this.cacheService.setSearchResults(
            siteId,
            queryString,
            query.page,
            query.pageSize,
            results
          );
        }
      }),
      catchError(error => this.handleSearchError(error)),
      finalize(() => this.loadingSubject.next(false))
    );
  }

  /**
   * Clears the current search results
   */
  clearResults(): void {
    this.searchResultsSubject.next(EmptySearchResults);
    this.errorSubject.next('');
  }

  /**
   * Invalidates search cache to force fresh data on next search
   */
  invalidateCache(): void {
    this.cacheService.invalidateSearchCache();
  }

  /**
   * Gets the current search results without performing a new search
   * 
   * @returns Current search results
   */
  getCurrentResults(): SearchResults {
    return this.searchResultsSubject.value;
  }

  /**
   * Maps API response to the SearchResults format
   * 
   * @param response API response with interaction data
   * @param query Original search query
   * @returns Formatted search results
   */
  private mapResponseToSearchResults(
    response: SearchResultsResponse,
    query: SearchQuery
  ): SearchResults {
    // Map each interaction to a SearchResultItem
    const items: SearchResultItem[] = response.interactions.map(interaction => ({
      id: interaction.id,
      title: interaction.title,
      type: interaction.type,
      lead: interaction.lead,
      startDatetime: new Date(interaction.startDatetime),
      endDatetime: new Date(interaction.endDatetime),
      timezone: interaction.timezone,
      location: interaction.location || '',
      siteId: interaction.siteId,
      siteName: interaction.site?.name || ''
    }));

    // Create metadata object with pagination and performance information
    const metadata = {
      total: response.total,
      page: response.page,
      pageSize: response.pageSize,
      pages: response.pages || Math.ceil(response.total / response.pageSize),
      executionTimeMs: response.executionTimeMs || 0
    };

    // Construct and return a SearchResults object
    return {
      items,
      metadata,
      query,
      loading: false
    };
  }

  /**
   * Handles errors that occur during search operations
   * 
   * @param error The error that occurred
   * @returns Observable with empty search results
   */
  private handleSearchError(error: any): Observable<SearchResults> {
    // Extract error message from error object
    let errorMessage = 'An error occurred while searching';
    
    if (error && error.message) {
      errorMessage = error.message;
    } else if (typeof error === 'string') {
      errorMessage = error;
    }
    
    // Set errorSubject with the formatted error message
    this.errorSubject.next(errorMessage);
    console.error('Search error:', error);
    
    // Return empty search results
    return of({
      ...EmptySearchResults,
      loading: false
    });
  }
}