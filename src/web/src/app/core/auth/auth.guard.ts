import { Injectable } from '@angular/core'; // v16.2.0
import { Router, CanActivate, CanActivateChild, CanActivateFn, ActivatedRouteSnapshot, RouterStateSnapshot, UrlTree } from '@angular/router'; // v16.2.0
import { Observable } from 'rxjs'; // v7.8.1
import { map, take } from 'rxjs/operators'; // v7.8.1
import { AuthService } from './auth.service';

/**
 * Functional implementation of the authentication guard using the modern Angular approach.
 * Prevents unauthorized access to protected routes by checking if the user is authenticated.
 * 
 * @param route The route being activated
 * @param state The router state snapshot
 * @returns Observable that resolves to true if user is authenticated, or redirects to login page if not
 */
export const authGuardFn: CanActivateFn = (
  route: ActivatedRouteSnapshot, 
  state: RouterStateSnapshot
): Observable<boolean | UrlTree> => {
  const authService = inject(AuthService);
  const router = inject(Router);

  return authService.isAuthenticated().pipe(
    map(isAuthenticated => {
      // If user is authenticated, allow access to the route
      if (isAuthenticated) {
        return true;
      }
      
      // Otherwise redirect to the login page with the attempted URL as return URL
      return router.parseUrl('/auth/login');
    }),
    take(1) // Complete the observable after the first emission
  );
};

/**
 * Legacy class-based authentication guard that implements CanActivate and CanActivateChild interfaces.
 * Provides the same functionality as the functional guard but using the traditional class-based approach
 * for backward compatibility with older Angular code.
 */
@Injectable({
  providedIn: 'root'
})
export class AuthGuard implements CanActivate, CanActivateChild {
  /**
   * Creates an instance of AuthGuard.
   * 
   * @param authService Service for checking authentication status
   * @param router Router for navigation if authentication fails
   */
  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  /**
   * Determines if a route can be activated based on authentication status.
   * 
   * @param route The route attempting to be accessed
   * @param state The router state
   * @returns Observable that resolves to true if authenticated, or redirects to login page if not
   */
  canActivate(
    route: ActivatedRouteSnapshot,
    state: RouterStateSnapshot
  ): Observable<boolean | UrlTree> {
    return this.authService.isAuthenticated().pipe(
      map(isAuthenticated => {
        if (isAuthenticated) {
          return true;
        }
        
        // Redirect to login page
        return this.router.parseUrl('/auth/login');
      }),
      take(1) // Complete the observable after the first emission
    );
  }

  /**
   * Determines if child routes can be activated based on authentication status.
   * Uses the same logic as canActivate for consistent behavior.
   * 
   * @param childRoute The child route attempting to be accessed
   * @param state The router state
   * @returns Observable that resolves to true if authenticated, or redirects to login page if not
   */
  canActivateChild(
    childRoute: ActivatedRouteSnapshot,
    state: RouterStateSnapshot
  ): Observable<boolean | UrlTree> {
    return this.canActivate(childRoute, state);
  }
}