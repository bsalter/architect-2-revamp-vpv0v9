/**
 * Site entity interfaces for the Interaction Management System
 * These interfaces define the structure of site-related data used throughout the frontend application.
 * They support site-scoped access control by providing strongly-typed structures for site data.
 */

/**
 * Represents a site entity in the system
 * Used for displaying site details and supporting site-scoped access control
 */
export interface Site {
  /** Unique identifier for the site */
  id: number;
  /** Display name of the site */
  name: string;
  /** Optional description of the site purpose or location */
  description?: string;
  /** When the site was created in ISO format */
  created_at: string;
  /** When the site was last updated in ISO format */
  updated_at: string;
  /** Number of users associated with this site */
  user_count?: number;
  /** Number of interactions recorded for this site */
  interaction_count?: number;
}

/**
 * Extends the Site interface to include the user's role for the site
 * Used in site selection screens and for authorization checks
 */
export interface SiteWithRole {
  /** Unique identifier for the site */
  id: number;
  /** Display name of the site */
  name: string;
  /** Optional description of the site purpose or location */
  description?: string;
  /** User's role within this site (e.g., 'admin', 'user', 'viewer') */
  role: string;
}

/**
 * Simplified site representation for dropdown selections and other UI components
 * Where only basic site information is needed
 */
export interface SiteOption {
  /** Unique identifier for the site */
  id: number;
  /** Display name of the site */
  name: string;
}

/**
 * Represents paginated site list responses from the API
 * Used primarily in site administration functions
 */
export interface SiteListResponse {
  /** Array of site items */
  items: Site[];
  /** Total number of sites matching the query */
  total: number;
  /** Current page number */
  page: number;
  /** Number of items per page */
  page_size: number;
  /** Total number of pages */
  pages: number;
}

/**
 * Defines the structure for site creation requests
 * Used in site administration functions
 */
export interface SiteCreate {
  /** Name for the new site (required) */
  name: string;
  /** Optional description for the new site */
  description?: string;
}

/**
 * Defines the structure for site update requests
 * Used in site administration functions
 */
export interface SiteUpdate {
  /** Updated name for the site */
  name?: string;
  /** Updated description for the site */
  description?: string;
}

/**
 * Represents the current site context information throughout the application
 * Used to maintain the user's currently selected site
 */
export interface SiteContext {
  /** ID of the currently selected site */
  site_id: number;
  /** Name of the currently selected site */
  name: string;
  /** User's role within the currently selected site */
  role: string;
}