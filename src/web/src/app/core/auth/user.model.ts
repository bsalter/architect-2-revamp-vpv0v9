/**
 * User model and related types for authentication and authorization
 * 
 * This file defines the core user entity structure and authorization models
 * that support site-scoped access control throughout the application.
 */

import { SiteWithRole } from '../../../features/sites/models/site.model';

/**
 * Enum defining the possible user roles for site-based permissions
 * Used for role-based access control throughout the application
 * 
 * The role hierarchy is:
 * SITE_ADMIN > EDITOR > VIEWER
 */
export enum UserRoleEnum {
  /** Can manage site settings and users, full access to site data */
  SITE_ADMIN = 'site_admin',
  /** Can create and modify interactions */
  EDITOR = 'editor',
  /** Read-only access to interactions */
  VIEWER = 'viewer'
}

/**
 * Interface defining the structure of user claims in JWT tokens
 * Maps to the token structure provided by Auth0 integration
 */
export interface UserTokenClaims {
  /** User identifier (usually Auth0 user ID) */
  sub: string;
  /** User's full name */
  name: string;
  /** User's email address */
  email: string;
  /** Array of site IDs the user has access to */
  sites: number[];
  /** Map of site IDs to roles (e.g., {"1": "site_admin", "2": "editor"}) */
  site_roles: { [siteId: string]: string };
  /** Token issuer (Auth0 URL) */
  iss: string;
  /** Issued at timestamp */
  iat: number;
  /** Expiration timestamp */
  exp: number;
}

/**
 * Class representing an authenticated user with site-scoped access rights
 * Provides methods for permission checking and site context management
 */
export class User {
  /** Unique identifier for the user */
  id: string;
  /** Username for display purposes */
  username: string;
  /** User's email address */
  email: string;
  /** Array of sites the user has access to with associated roles */
  sites: SiteWithRole[];
  /** Currently selected site ID */
  currentSiteId: number | null;
  /** Whether the user is currently authenticated */
  isAuthenticated: boolean;
  /** When the user last logged in */
  lastLogin: Date | null;

  /**
   * Creates a new User instance with the provided user data
   * 
   * @param userData Object containing user properties from authentication
   */
  constructor(userData: Partial<User>) {
    this.id = userData.id || '';
    this.username = userData.username || '';
    this.email = userData.email || '';
    this.sites = userData.sites || [];
    this.isAuthenticated = true;
    this.currentSiteId = userData.currentSiteId || (this.sites.length > 0 ? this.sites[0].id : null);
    this.lastLogin = userData.lastLogin || new Date();
  }

  /**
   * Returns an array of site IDs that the user has access to
   * 
   * @returns Array of site IDs accessible to the user
   */
  getSiteIds(): number[] {
    return this.sites.map(site => site.id);
  }

  /**
   * Checks if the user has access to a specific site
   * 
   * @param siteId ID of the site to check access for
   * @returns True if user has access to the specified site
   */
  hasSiteAccess(siteId: number): boolean {
    return this.getSiteIds().includes(siteId);
  }

  /**
   * Gets the user's role for a specific site
   * 
   * @param siteId ID of the site to get the role for
   * @returns The user's role for the site or null if no access
   */
  getSiteRole(siteId: number): string | null {
    const site = this.sites.find(s => s.id === siteId);
    return site ? site.role : null;
  }

  /**
   * Checks if the user has a specific role or higher for a site
   * Uses the role hierarchy: SITE_ADMIN > EDITOR > VIEWER
   * 
   * @param siteId ID of the site to check role for
   * @param requiredRole The minimum role required
   * @returns True if user has the required role or higher
   */
  hasRoleForSite(siteId: number, requiredRole: string): boolean {
    const userRole = this.getSiteRole(siteId);
    if (!userRole) return false;

    // Define role hierarchy for comparison
    const roleHierarchy = {
      [UserRoleEnum.SITE_ADMIN]: 3,
      [UserRoleEnum.EDITOR]: 2,
      [UserRoleEnum.VIEWER]: 1
    };

    // Get the numeric values for comparison
    const userRoleValue = roleHierarchy[userRole as keyof typeof roleHierarchy] || 0;
    const requiredRoleValue = roleHierarchy[requiredRole as keyof typeof roleHierarchy] || 0;

    // User has sufficient permissions if their role value is >= required role value
    return userRoleValue >= requiredRoleValue;
  }

  /**
   * Sets the current active site for the user
   * Validates that the user has access to the site before setting
   * 
   * @param siteId ID of the site to set as current
   * @returns True if site was set successfully, false if user lacks access
   */
  setCurrentSite(siteId: number): boolean {
    if (!this.hasSiteAccess(siteId)) {
      return false;
    }
    
    this.currentSiteId = siteId;
    return true;
  }

  /**
   * Gets the current site information including role
   * 
   * @returns Current site with role or null if none selected
   */
  getCurrentSite(): SiteWithRole | null {
    if (!this.currentSiteId) {
      return null;
    }
    
    return this.sites.find(site => site.id === this.currentSiteId) || null;
  }
}