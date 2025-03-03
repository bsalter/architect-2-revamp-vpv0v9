import { Injectable } from '@angular/core'; // v16.2.0
import { Router } from '@angular/router'; // v16.2.0
import { Observable, BehaviorSubject, from, of } from 'rxjs'; // v7.8.1
import { catchError, tap, switchMap, finalize } from 'rxjs/operators'; // v7.8.1
import { Auth0Client } from '@auth0/auth0-spa-js'; // v2.1.2

import { User, UserTokenClaims } from './user.model';
import { TokenService } from './token.service';
import { UserContextService } from './user-context.service';
import { SiteSelectionService } from './site-selection.service';
import { Auth0Config, createAuth0Config } from './auth0-config';
import { ApiService } from '../http/api.service';
import { environment } from '../../../environments/environment';

/**
 * Primary service responsible for managing authentication state, handling Auth0 integration,
 * login/logout flows, and coordinating with other services for site access control.
 * 
 * Implements the requirements for User Authentication (F-001) and supports Site-Scoped
 * Access Control (F-002) by integrating with Auth0 and managing JWT tokens.
 */
@Injectable({
  providedIn: 'root'
})
export class AuthService {
  /**
   * Auth0 client instance for authentication operations
   */
  private auth0Client: Auth0Client | null = null;

  /**
   * BehaviorSubject tracking whether authentication is in progress
   */
  private isAuthenticatingSubject = new BehaviorSubject<boolean>(false);
  public isAuthenticating$ = this.isAuthenticatingSubject.asObservable();

  /**
   * BehaviorSubject tracking whether the Auth0 client has been initialized
   */
  private isInitializedSubject = new BehaviorSubject<boolean>(false);
  public isInitialized$ = this.isInitializedSubject.asObservable();

  /**
   * Auth0 configuration settings
   */
  private auth0Config: Auth0Config;

  /**
   * Initializes the auth service and sets up Auth0 client
   * 
   * @param router Angular router for navigation
   * @param tokenService Service for JWT token management
   * @param userContextService Service for managing user context
   * @param siteSelectionService Service for site selection workflow
   * @param apiService Service for making API calls
   */
  constructor(
    private router: Router,
    private tokenService: TokenService,
    private userContextService: UserContextService,
    private siteSelectionService: SiteSelectionService,
    private apiService: ApiService
  ) {
    // Get Auth0 configuration
    this.auth0Config = createAuth0Config();
    
    // Initialize Auth0 client
    this.initializeAuth0Client().catch(error => {
      console.error('Error initializing Auth0 client:', error);
    });
    
    // Subscribe to authentication state changes from token service
    this.tokenService.isAuthenticated$.subscribe(isAuthenticated => {
      if (!isAuthenticated) {
        // Clear user context when authentication is lost
        this.userContextService.clearUserContext();
      }
    });
  }

  /**
   * Initializes the Auth0 client with configuration and checks for existing session
   * 
   * @returns Promise that resolves when initialization is complete
   */
  private async initializeAuth0Client(): Promise<void> {
    this.isInitializedSubject.next(false);
    
    try {
      // Create Auth0 client instance
      this.auth0Client = new Auth0Client({
        domain: this.auth0Config.domain,
        clientId: this.auth0Config.clientId,
        authorizationParams: {
          redirect_uri: this.auth0Config.redirectUri,
          audience: this.auth0Config.audience,
          scope: this.auth0Config.scope
        },
        cacheLocation: this.auth0Config.cacheLocation,
        useRefreshTokens: this.auth0Config.useRefreshTokens
      });
      
      // Check if we're in a callback from Auth0
      if (window.location.search.includes('code=') && 
          window.location.search.includes('state=')) {
        // Don't perform any additional initialization here
        // The callback will be handled separately by the component
      } else {
        try {
          // Try to get a token silently - will succeed if user has an active session
          const token = await this.auth0Client.getTokenSilently();
          
          if (token) {
            // Store token
            this.tokenService.setToken(token);
            
            // Get user info from token
            const user = this.tokenService.getUserFromToken(token);
            
            if (user) {
              // Update user context
              this.userContextService.setCurrentUser(user);
              
              // Check if site selection is required
              this.siteSelectionService.checkSiteSelectionRequired();
            }
          }
        } catch (error) {
          // Silent authentication failed, user needs to log in
          console.log('Silent authentication failed:', error);
        }
      }
    } catch (error) {
      console.error('Error during Auth0 client initialization:', error);
      throw error;
    } finally {
      this.isInitializedSubject.next(true);
    }
  }

  /**
   * Initiates the Auth0 login process
   * 
   * @returns Observable that completes when login is successful
   */
  login(): Observable<void> {
    this.isAuthenticatingSubject.next(true);
    
    return new Observable<void>(observer => {
      if (!this.auth0Client) {
        observer.error(new Error('Auth0 client not initialized'));
        this.isAuthenticatingSubject.next(false);
        return;
      }
      
      try {
        // Start login flow with redirect
        this.auth0Client.loginWithRedirect({
          authorizationParams: {
            redirect_uri: this.auth0Config.redirectUri
          }
        });
        
        // Observer will never complete as page will redirect
        observer.next();
      } catch (error) {
        observer.error(error);
        this.isAuthenticatingSubject.next(false);
      }
    }).pipe(
      catchError(error => {
        this.isAuthenticatingSubject.next(false);
        return this.handleAuthenticationError(error);
      })
    );
  }

  /**
   * Processes Auth0 redirect callback after successful authentication
   * 
   * @returns Observable that completes when callback processing is done
   */
  handleRedirectCallback(): Observable<void> {
    this.isAuthenticatingSubject.next(true);
    
    if (!this.auth0Client) {
      return of(undefined).pipe(
        tap(() => {
          console.error('Auth0 client not initialized');
          this.router.navigate(['/login']);
        }),
        finalize(() => this.isAuthenticatingSubject.next(false))
      );
    }
    
    return from(this.auth0Client.handleRedirectCallback()).pipe(
      switchMap(() => from(this.auth0Client!.getTokenSilently())),
      switchMap(token => {
        // Store token
        this.tokenService.setToken(token);
        
        // Get user from token
        const user = this.tokenService.getUserFromToken(token);
        
        if (!user) {
          return of(undefined).pipe(
            tap(() => {
              console.error('Could not extract user from token');
              this.router.navigate(['/login']);
            })
          );
        }
        
        // Update user context
        this.userContextService.setCurrentUser(user);
        
        // Check if site selection is required
        const requiresSiteSelection = this.siteSelectionService.checkSiteSelectionRequired();
        
        if (requiresSiteSelection) {
          // Navigate to site selection page
          this.siteSelectionService.startSiteSelection('/dashboard');
        } else {
          // Navigate to dashboard
          this.router.navigate(['/dashboard']);
        }
        
        return of(undefined);
      }),
      catchError(error => {
        return this.handleAuthenticationError(error).pipe(
          tap(() => {
            this.router.navigate(['/login']);
          })
        );
      }),
      finalize(() => this.isAuthenticatingSubject.next(false))
    );
  }

  /**
   * Logs out the current user from both the application and Auth0
   * 
   * @returns Observable that completes when logout is successful
   */
  logout(): Observable<void> {
    return new Observable<void>(observer => {
      if (!this.auth0Client) {
        observer.error(new Error('Auth0 client not initialized'));
        return;
      }
      
      try {
        // Clear tokens and user context
        this.tokenService.removeToken();
        this.userContextService.clearUserContext();
        this.siteSelectionService.cancelSiteSelection();
        
        // Redirect to Auth0 logout URL
        this.auth0Client.logout({
          logoutParams: {
            returnTo: this.auth0Config.logoutRedirectUri
          }
        });
        
        observer.next();
        observer.complete();
      } catch (error) {
        observer.error(error);
      }
    }).pipe(
      catchError(error => this.handleAuthenticationError(error))
    );
  }

  /**
   * Refreshes the Auth0 session to maintain authentication
   * 
   * @returns Observable that emits new access token
   */
  refreshSession(): Observable<string> {
    if (!this.auth0Client) {
      return of('').pipe(
        tap(() => {
          console.error('Auth0 client not initialized');
          this.router.navigate(['/login']);
        })
      );
    }
    
    return from(this.auth0Client.getTokenSilently()).pipe(
      tap(token => {
        // Store the refreshed token
        this.tokenService.setToken(token);
      }),
      catchError(error => {
        // Handle specific token errors
        if (error.error === 'login_required' || 
            error.error === 'consent_required' ||
            error.error === 'interaction_required') {
          // User needs to re-authenticate
          this.tokenService.removeToken();
          this.userContextService.clearUserContext();
          
          // Redirect to login page
          this.router.navigate(['/login']);
          return of('');
        }
        
        return this.handleAuthenticationError(error).pipe(
          switchMap(() => of(''))
        );
      })
    );
  }

  /**
   * Checks if user is currently authenticated
   * 
   * @returns Observable that emits authentication state
   */
  isAuthenticated(): Observable<boolean> {
    return this.tokenService.isAuthenticated$;
  }

  /**
   * Gets the current authenticated user
   * 
   * @returns Observable that emits the current user or null
   */
  getUser(): Observable<User | null> {
    return this.userContextService.currentUser$;
  }

  /**
   * Handles authentication-related errors
   * 
   * @param error The error to handle
   * @returns Observable that completes without emitting
   */
  private handleAuthenticationError(error: Error): Observable<never> {
    console.error('Authentication error:', error);
    
    // Check for specific error types
    if (error.message?.includes('expired') || 
        error.message?.includes('invalid token')) {
      // Clear tokens and user context for authentication errors
      this.tokenService.removeToken();
      this.userContextService.clearUserContext();
    }
    
    return of(undefined).pipe(
      tap(() => {}),
      // This is just to satisfy TypeScript, the Observable will never emit
      switchMap(() => { throw error; })
    );
  }
}