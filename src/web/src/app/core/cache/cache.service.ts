import { Injectable } from '@angular/core'; // v16.2.0
import { Observable, of } from 'rxjs'; // v7.8.1
import * as CacheKeys from './cache-keys';

/**
 * Service that provides caching functionality for the application
 * with support for memory and localStorage caching with TTL
 */
@Injectable({
  providedIn: 'root'
})
export class CacheService {
  private memoryCache: Map<string, { value: any, expiry: number }> = new Map();

  constructor() {
    // Initialize empty memory cache
  }

  /**
   * Retrieves data from cache by key, checking expiry time
   * 
   * @param key - The cache key to retrieve
   * @returns The cached value or null if not found or expired
   */
  get(key: string): any | null {
    // First try memory cache
    const cachedItem = this.memoryCache.get(key);
    
    if (cachedItem && !this.isExpired(cachedItem.expiry)) {
      return cachedItem.value;
    }
    
    // If not in memory or expired, remove it from memory cache
    if (cachedItem) {
      this.memoryCache.delete(key);
    }
    
    // Try localStorage as fallback
    try {
      const storedItem = localStorage.getItem(key);
      if (storedItem) {
        const parsedItem = JSON.parse(storedItem);
        if (!this.isExpired(parsedItem.expiry)) {
          // Refresh memory cache with localStorage data
          this.memoryCache.set(key, parsedItem);
          return parsedItem.value;
        } else {
          // Remove expired item from localStorage
          localStorage.removeItem(key);
        }
      }
    } catch (error) {
      console.error('Error retrieving from localStorage:', error);
    }
    
    return null;
  }

  /**
   * Stores data in cache with specified TTL
   * 
   * @param key - The cache key to store
   * @param value - The value to cache
   * @param ttl - Time to live in milliseconds
   */
  set(key: string, value: any, ttl: number): void {
    const now = new Date().getTime();
    const expiry = now + ttl;
    const cacheItem = { value, expiry };
    
    // Store in memory cache
    this.memoryCache.set(key, cacheItem);
    
    // Try to store in localStorage if serializable
    try {
      localStorage.setItem(key, JSON.stringify(cacheItem));
    } catch (error) {
      console.error('Error storing in localStorage:', error);
    }
  }

  /**
   * Removes data from cache by key
   * 
   * @param key - The cache key to remove
   */
  remove(key: string): void {
    this.memoryCache.delete(key);
    
    try {
      localStorage.removeItem(key);
    } catch (error) {
      console.error('Error removing from localStorage:', error);
    }
  }

  /**
   * Clears all cached data
   */
  clear(): void {
    this.memoryCache.clear();
    
    try {
      // Only clear cache-related items, not all localStorage
      Object.keys(localStorage)
        .filter(key => 
          key.startsWith(CacheKeys.PREFIX_AUTH) ||
          key.startsWith(CacheKeys.PREFIX_SITE) ||
          key.startsWith(CacheKeys.PREFIX_INTERACTION) ||
          key.startsWith(CacheKeys.PREFIX_SEARCH) ||
          key.startsWith(CacheKeys.PREFIX_USER_SITES)
        )
        .forEach(key => localStorage.removeItem(key));
    } catch (error) {
      console.error('Error clearing localStorage:', error);
    }
  }

  /**
   * Clears all cached data with keys starting with the specified prefix
   * 
   * @param prefix - The prefix to match for clearing cache entries
   */
  clearByPrefix(prefix: string): void {
    // Clear memory cache with matching prefix
    for (const key of this.memoryCache.keys()) {
      if (key.startsWith(prefix)) {
        this.memoryCache.delete(key);
      }
    }
    
    // Clear localStorage with matching prefix
    try {
      Object.keys(localStorage)
        .filter(key => key.startsWith(prefix))
        .forEach(key => localStorage.removeItem(key));
    } catch (error) {
      console.error('Error clearing localStorage by prefix:', error);
    }
  }

  /**
   * Retrieves a cached interaction by ID
   * 
   * @param id - The interaction ID
   * @returns The cached interaction or null if not found
   */
  getInteraction(id: number): any | null {
    const key = CacheKeys.getInteractionDetailKey(id);
    return this.get(key);
  }

  /**
   * Caches an interaction by ID
   * 
   * @param id - The interaction ID
   * @param interaction - The interaction data to cache
   */
  setInteraction(id: number, interaction: any): void {
    const key = CacheKeys.getInteractionDetailKey(id);
    this.set(key, interaction, CacheKeys.INTERACTION_CACHE_DURATION);
  }

  /**
   * Retrieves cached interaction list for specified site and pagination parameters
   * 
   * @param siteId - The site ID
   * @param page - Page number
   * @param pageSize - Items per page
   * @returns The cached interaction list or null if not found
   */
  getInteractions(siteId: number, page: number, pageSize: number): any | null {
    const key = CacheKeys.getInteractionListKey(siteId, page, pageSize);
    return this.get(key);
  }

  /**
   * Caches a list of interactions with pagination parameters
   * 
   * @param siteId - The site ID
   * @param page - Page number
   * @param pageSize - Items per page
   * @param interactions - The interaction list data to cache
   */
  setInteractions(siteId: number, page: number, pageSize: number, interactions: any): void {
    const key = CacheKeys.getInteractionListKey(siteId, page, pageSize);
    this.set(key, interactions, CacheKeys.INTERACTION_CACHE_DURATION);
  }

  /**
   * Retrieves cached search results for specified parameters
   * 
   * @param siteId - The site ID
   * @param query - Search query string
   * @param page - Page number
   * @param pageSize - Items per page
   * @returns The cached search results or null if not found
   */
  getSearchResults(siteId: number, query: string, page: number, pageSize: number): any | null {
    const key = CacheKeys.getSearchResultsKey(siteId, query, page, pageSize);
    return this.get(key);
  }

  /**
   * Caches search results for specified parameters
   * 
   * @param siteId - The site ID
   * @param query - Search query string
   * @param page - Page number
   * @param pageSize - Items per page
   * @param results - The search results data to cache
   */
  setSearchResults(siteId: number, query: string, page: number, pageSize: number, results: any): void {
    const key = CacheKeys.getSearchResultsKey(siteId, query, page, pageSize);
    this.set(key, results, CacheKeys.SEARCH_CACHE_DURATION);
  }

  /**
   * Invalidates all interaction-related cache entries
   */
  invalidateInteractionCache(): void {
    this.clearByPrefix(CacheKeys.PREFIX_INTERACTION);
    this.clearByPrefix(CacheKeys.PREFIX_INTERACTION_LIST);
  }

  /**
   * Invalidates all search-related cache entries
   */
  invalidateSearchCache(): void {
    this.clearByPrefix(CacheKeys.PREFIX_SEARCH);
  }

  /**
   * Invalidates all authentication-related cache entries
   */
  invalidateAuthCache(): void {
    this.clearByPrefix(CacheKeys.PREFIX_AUTH);
  }

  /**
   * Invalidates all site-related cache entries
   */
  invalidateSiteCache(): void {
    this.clearByPrefix(CacheKeys.PREFIX_SITE);
    this.clearByPrefix(CacheKeys.PREFIX_USER_SITES);
  }

  /**
   * Checks if a cache entry is expired based on its expiry timestamp
   * 
   * @param expiry - The expiry timestamp to check
   * @returns True if expired, false if still valid
   * @private
   */
  private isExpired(expiry: number): boolean {
    return new Date().getTime() > expiry;
  }
}