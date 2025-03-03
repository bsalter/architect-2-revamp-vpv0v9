import { Injectable } from '@angular/core'; // v16.2.0
import { Observable, BehaviorSubject, of } from 'rxjs'; // v7.8.1
import { map } from 'rxjs/operators'; // v7.8.1
import jwtDecode from 'jwt-decode'; // v3.1.2

import { User, UserTokenClaims } from './user.model';
import { CacheService } from '../cache/cache.service';
import * as CacheKeys from '../cache/cache-keys';
import { environment } from 'src/environments/environment';

/**
 * Service responsible for JWT token management, including storage, retrieval,
 * validation, and decoding user information from tokens.
 * 
 * Implements token-based authentication to maintain user sessions across
 * the application with support for site-scoped access control.
 */
@Injectable({
  providedIn: 'root'
})
export class TokenService {
  // Private BehaviorSubjects to track token and auth state
  private tokenSubject = new BehaviorSubject<string | null>(null);
  // Public Observables for components to subscribe to
  public token$ = this.tokenSubject.asObservable();
  
  private isAuthenticatedSubject = new BehaviorSubject<boolean>(false);
  public isAuthenticated$ = this.isAuthenticatedSubject.asObservable();

  /**
   * Creates an instance of TokenService.
   * Automatically attempts to restore any cached token to maintain
   * authentication state across page refreshes.
   * 
   * @param cacheService The cache service for token storage
   */
  constructor(private cacheService: CacheService) {
    // Try to restore token from cache when service initializes
    this.refreshTokenFromCache();
  }

  /**
   * Gets the current JWT token
   * 
   * @returns Current JWT token or null if not authenticated
   */
  getToken(): string | null {
    return this.tokenSubject.value;
  }

  /**
   * Sets a new JWT token and updates authentication state
   * 
   * @param token The JWT token to set
   */
  setToken(token: string): void {
    this.tokenSubject.next(token);
    // Store token in cache with appropriate TTL
    this.cacheService.set(CacheKeys.AUTH_TOKEN_KEY, token, CacheKeys.AUTH_CACHE_DURATION);
    this.isAuthenticatedSubject.next(true);
    
    // Debug log in development only
    if (!environment.production) {
      console.log('Token set and cached');
    }
  }

  /**
   * Removes the JWT token and clears authentication state
   */
  removeToken(): void {
    this.tokenSubject.next(null);
    this.cacheService.remove(CacheKeys.AUTH_TOKEN_KEY);
    this.isAuthenticatedSubject.next(false);
    
    // Debug log in development only
    if (!environment.production) {
      console.log('Token removed from cache');
    }
  }

  /**
   * Checks if the current token is expired
   * 
   * @returns True if token is expired or invalid, false if valid
   */
  isTokenExpired(): boolean {
    const token = this.getToken();
    if (!token) {
      return true;
    }
    
    try {
      const expDate = this.getTokenExpirationDate(token);
      return expDate ? expDate <= new Date() : true;
    } catch (error) {
      console.error('Error checking token expiration:', error);
      return true;
    }
  }

  /**
   * Decodes the JWT token to extract claims
   * 
   * @param token The JWT token to decode
   * @returns Decoded token claims or null if invalid
   */
  decodeToken(token: string): UserTokenClaims | null {
    if (!token) {
      return null;
    }
    
    try {
      return jwtDecode<UserTokenClaims>(token);
    } catch (error) {
      console.error('Error decoding token:', error);
      return null;
    }
  }

  /**
   * Extracts user information from the JWT token
   * 
   * @param token The JWT token to extract user info from
   * @returns User object created from token claims or null if invalid
   */
  getUserFromToken(token: string | null): User | null {
    if (!token) {
      return null;
    }
    
    const decodedToken = this.decodeToken(token);
    if (!decodedToken) {
      return null;
    }
    
    // Map token claims to User object properties
    const userData: Partial<User> = {
      id: decodedToken.sub,
      username: decodedToken.name,
      email: decodedToken.email,
      isAuthenticated: true,
      lastLogin: new Date()
    };
    
    // Map site IDs and roles
    if (decodedToken.sites && decodedToken.site_roles) {
      userData.sites = decodedToken.sites.map(siteId => {
        return {
          id: siteId,
          name: '', // Name might be populated later from API
          description: undefined, // Not available in token
          role: decodedToken.site_roles[siteId.toString()] || 'viewer' // Default to viewer
        };
      });
      
      // Set current site to first available site if any
      if (userData.sites && userData.sites.length > 0) {
        userData.currentSiteId = userData.sites[0].id;
      }
    }
    
    return new User(userData);
  }

  /**
   * Gets the expiration date from a JWT token
   * 
   * @param token The JWT token to get expiration date from
   * @returns Token expiration date or null if invalid
   */
  getTokenExpirationDate(token: string): Date | null {
    const decodedToken = this.decodeToken(token);
    if (!decodedToken || !decodedToken.exp) {
      return null;
    }
    
    // Convert exp timestamp to Date (JWT exp is in seconds, Date takes milliseconds)
    return new Date(decodedToken.exp * 1000);
  }

  /**
   * Attempts to restore token from cache
   * 
   * @returns True if token successfully restored, false otherwise
   */
  refreshTokenFromCache(): boolean {
    try {
      const cachedToken = this.cacheService.get(CacheKeys.AUTH_TOKEN_KEY);
      
      if (cachedToken) {
        // Check if token is not expired
        const expDate = this.getTokenExpirationDate(cachedToken);
        if (expDate && expDate > new Date()) {
          this.tokenSubject.next(cachedToken);
          this.isAuthenticatedSubject.next(true);
          return true;
        }
      }
      
      return false;
    } catch (error) {
      console.error('Error refreshing token from cache:', error);
      return false;
    }
  }
}