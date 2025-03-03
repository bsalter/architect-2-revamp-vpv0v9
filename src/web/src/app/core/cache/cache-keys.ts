/**
 * @file cache-keys.ts
 * 
 * This file defines constants and utility functions for the application's caching system.
 * It ensures consistent cache key generation and organization of cached data with 
 * appropriate Time-To-Live (TTL) durations.
 * 
 * The caching strategy follows the specifications outlined in the technical documentation,
 * with different TTL values for different types of data based on their update frequency 
 * and importance.
 */

import { environment } from 'src/environments/environment'; // v1.0.0

/**
 * Prefix constants for different categories of cache keys
 * Using prefixes helps organize and identify cache entries
 */
export const PREFIX_AUTH = 'auth-';
export const PREFIX_SITE = 'site-';
export const PREFIX_USER_SITES = 'user-sites-';
export const PREFIX_INTERACTION = 'interaction-';
export const PREFIX_INTERACTION_LIST = 'interaction-list-';
export const PREFIX_SEARCH = 'search-';

/**
 * Cache duration constants (in milliseconds)
 * These durations are set based on the technical specifications and can be adjusted
 * based on production usage patterns
 */
export const AUTH_CACHE_DURATION = 30 * 60 * 1000; // 30 minutes
export const SITE_CACHE_DURATION = 30 * 60 * 1000; // 30 minutes
export const INTERACTION_CACHE_DURATION = 10 * 60 * 1000; // 10 minutes
export const SEARCH_CACHE_DURATION = 2 * 60 * 1000; // 2 minutes

/**
 * Common cache keys for frequently accessed data
 */
export const AUTH_TOKEN_KEY = PREFIX_AUTH + 'token';
export const AUTH_USER_KEY = PREFIX_AUTH + 'user';
export const CURRENT_SITE_KEY = PREFIX_SITE + 'current';
export const USER_SITES_KEY = PREFIX_USER_SITES + 'list';

/**
 * Generates a cache key for storing individual interaction details
 * 
 * @param interactionId - The unique identifier of the interaction
 * @returns A string cache key for the specific interaction
 */
export function getInteractionDetailKey(interactionId: number): string {
  return `${PREFIX_INTERACTION}${interactionId}`;
}

/**
 * Generates a cache key for storing interaction lists with pagination parameters
 * 
 * @param siteId - The site identifier to scope the interaction list
 * @param page - The page number of the paginated results
 * @param pageSize - The number of items per page
 * @returns A string cache key including site and pagination information
 */
export function getInteractionListKey(siteId: number, page: number, pageSize: number): string {
  return `${PREFIX_INTERACTION_LIST}${siteId}-${page}-${pageSize}`;
}

/**
 * Generates a cache key for storing search results with query and pagination parameters
 * 
 * @param siteId - The site identifier to scope the search results
 * @param query - The search query string
 * @param page - The page number of the paginated results
 * @param pageSize - The number of items per page
 * @returns A string cache key including site, query string, and pagination information
 */
export function getSearchResultsKey(siteId: number, query: string, page: number, pageSize: number): string {
  // Encode the query string to prevent issues with special characters in cache keys
  const encodedQuery = encodeURIComponent(query);
  return `${PREFIX_SEARCH}${siteId}-${encodedQuery}-${page}-${pageSize}`;
}