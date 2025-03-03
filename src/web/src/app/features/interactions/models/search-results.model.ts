import { Interaction } from './interaction.model';
import { SearchQuery } from './filter.model';

/**
 * Interface representing a single interaction item in search results,
 * with essential properties for display in the Finder table.
 */
export interface SearchResultItem {
  /** Unique identifier for the interaction */
  id: number;
  /** Title/subject of the interaction */
  title: string;
  /** Type of interaction (meeting, call, email, etc.) */
  type: string;
  /** Primary person leading the interaction */
  lead: string;
  /** Start date and time of the interaction */
  startDatetime: Date;
  /** End date and time of the interaction */
  endDatetime: Date;
  /** Timezone the interaction takes place in */
  timezone: string;
  /** Physical or virtual location of the interaction */
  location: string;
  /** ID of the site this interaction belongs to */
  siteId: number;
  /** Name of the site this interaction belongs to */
  siteName: string;
}

/**
 * Interface for pagination and result metadata to support
 * UI elements like pagination controls.
 */
export interface SearchResultsMetadata {
  /** Total number of items matching the search criteria */
  total: number;
  /** Current page number (1-based) */
  page: number;
  /** Number of items per page */
  pageSize: number;
  /** Total number of pages */
  pages: number;
  /** Time taken to execute the search query in milliseconds */
  executionTimeMs: number;
}

/**
 * Main interface for search results combining items, metadata,
 * and query information.
 */
export interface SearchResults {
  /** Array of search result items */
  items: SearchResultItem[];
  /** Metadata about pagination and execution */
  metadata: SearchResultsMetadata;
  /** The query that produced these results */
  query: SearchQuery;
  /** Whether the search is currently in progress */
  loading: boolean;
}

/**
 * Interface matching the backend API response format for search results.
 */
export interface SearchResultsResponse {
  /** Array of interaction records */
  interactions: Interaction[];
  /** Total number of interactions matching the query */
  total: number;
  /** Current page number */
  page: number;
  /** Number of items per page */
  pageSize: number;
  /** Total number of pages */
  pages: number;
  /** Time taken to execute the search query in milliseconds */
  executionTimeMs: number;
}

/**
 * Default empty state for search results.
 * Provides initial values for search results when no search has been performed.
 */
export const EmptySearchResults: SearchResults = {
  items: [],
  metadata: {
    total: 0,
    page: 1,
    pageSize: 10,
    pages: 0,
    executionTimeMs: 0
  },
  query: {
    page: 1,
    pageSize: 10
  },
  loading: false
};