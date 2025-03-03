import { Injectable } from '@angular/core'; // v16.2.0
import { Router, ActivatedRoute } from '@angular/router'; // v16.2.0
import { FormBuilder, FormGroup, FormControl, Validators } from '@angular/forms'; // v16.2.0
import { Observable, BehaviorSubject, of } from 'rxjs'; // v7.8.1
import { catchError, tap, finalize } from 'rxjs/operators'; // v7.8.1

import { AuthService } from '../../../core/auth/auth.service';
import { TokenService } from '../../../core/auth/token.service';
import { SiteSelectionService } from '../../../core/auth/site-selection.service';
import { ToastService } from '../../../shared/services/toast.service';

/**
 * Service responsible for managing authentication page functionality including 
 * form handling, validation, submission, and navigation. This service bridges 
 * the authentication UI components with the core authentication services.
 */
@Injectable({
  providedIn: 'root'
})
export class AuthPageService {
  /**
   * Reactive form for the login interface
   */
  loginForm: FormGroup;
  
  /**
   * BehaviorSubject tracking form submission state
   */
  private isSubmittingSubject = new BehaviorSubject<boolean>(false);
  isSubmitting$ = this.isSubmittingSubject.asObservable();
  
  /**
   * BehaviorSubject tracking form validation errors
   */
  private formErrorsSubject = new BehaviorSubject<Record<string, string[]>>({});
  formErrors$ = this.formErrorsSubject.asObservable();
  
  /**
   * Creates an instance of the AuthPageService and initializes the login form.
   * Sets up form validation and error clearing on user input.
   * 
   * @param fb Angular FormBuilder service for creating reactive forms
   * @param authService Core authentication service
   * @param tokenService Token management service
   * @param siteSelectionService Service for managing site selection workflow
   * @param router Angular router for navigation
   * @param route Current activated route
   * @param toastService Service for displaying notifications
   */
  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
    private tokenService: TokenService,
    private siteSelectionService: SiteSelectionService,
    private router: Router,
    private route: ActivatedRoute,
    private toastService: ToastService
  ) {
    // Initialize the login form with required validators
    this.loginForm = this.fb.group({
      username: ['', [Validators.required, Validators.email]],
      password: ['', Validators.required],
      rememberMe: [false]
    });
    
    // Clear errors when form values change
    this.loginForm.valueChanges.subscribe(() => {
      if (this.loginForm.dirty) {
        this.formErrorsSubject.next({});
      }
    });
  }

  /**
   * Handles the login form submission process.
   * Validates the form, shows errors if invalid, and initiates 
   * the Auth0 authentication flow if valid.
   * 
   * @returns Observable that completes when login is processed
   */
  handleLoginSubmit(): Observable<void> {
    // Validate form before submission
    if (!this.validateForm()) {
      // Return empty observable if validation fails
      return of(undefined);
    }
    
    // Set loading state
    this.isSubmittingSubject.next(true);
    
    // Initiate Auth0 login flow - this will redirect to Auth0
    return this.authService.login().pipe(
      catchError(error => {
        return this.handleAuthenticationError(error);
      }),
      finalize(() => {
        this.isSubmittingSubject.next(false);
      })
    );
  }

  /**
   * Handles forgot password request.
   * Currently shows an informational toast message as password reset
   * functionality is typically handled by Auth0.
   */
  handleForgotPassword(): void {
    this.toastService.showInfo(
      'You will be redirected to reset your password. Please follow the instructions on the next screen.',
      { title: 'Password Reset' }
    );
    
    // In a production implementation, this would redirect to Auth0's password reset page
    // or use Auth0's password reset API
  }

  /**
   * Checks for and handles authentication redirect callback from Auth0.
   * Processes the callback data and navigates to the appropriate page on success.
   * 
   * @returns Observable that emits true if callback was handled, false otherwise
   */
  checkAndHandleAuthRedirect(): Observable<boolean> {
    // Check if current URL contains Auth0 callback parameters
    if (window.location.search.includes('code=') && 
        window.location.search.includes('state=')) {
      
      // Process the callback with Auth0
      return this.authService.handleRedirectCallback().pipe(
        tap(() => {
          // Navigate to appropriate page on success
          this.handleAuthenticationSuccess();
        }),
        catchError(error => {
          return this.handleAuthenticationError(error);
        }),
        map(() => true) // Indicate that a redirect was handled
      );
    }
    
    // No redirect parameters found
    return of(false);
  }

  /**
   * Gets validation errors for a specific form control.
   * 
   * @param controlName Name of the form control
   * @returns Array of error messages for the control
   */
  getFormControlErrors(controlName: string): string[] {
    const control = this.loginForm.get(controlName);
    if (!control || !control.errors || !control.touched) {
      return [];
    }
    
    const errors: string[] = [];
    
    // Generate user-friendly error messages based on validation errors
    if (control.errors.required) {
      errors.push(`${controlName.charAt(0).toUpperCase() + controlName.slice(1)} is required`);
    }
    
    if (control.errors.email) {
      errors.push('Please enter a valid email address');
    }
    
    return errors;
  }

  /**
   * Validates the entire form and updates error state.
   * Marks all controls as touched to trigger validation display.
   * 
   * @returns True if form is valid, false otherwise
   */
  validateForm(): boolean {
    // Mark all fields as touched to trigger validation
    Object.keys(this.loginForm.controls).forEach(key => {
      const control = this.loginForm.get(key);
      if (control) {
        control.markAsTouched();
      }
    });
    
    // Check form validity
    if (!this.loginForm.valid) {
      // Collect all validation errors
      const errorMessages: Record<string, string[]> = {};
      
      Object.keys(this.loginForm.controls).forEach(key => {
        const errors = this.getFormControlErrors(key);
        if (errors.length > 0) {
          errorMessages[key] = errors;
        }
      });
      
      // Update error state
      this.formErrorsSubject.next(errorMessages);
      return false;
    }
    
    return true;
  }

  /**
   * Resets the login form to its initial state.
   * Clears all values, errors, and touched/dirty states.
   */
  resetForm(): void {
    this.loginForm.reset({ rememberMe: false });
    this.formErrorsSubject.next({});
    
    // Clear touched and dirty states
    Object.keys(this.loginForm.controls).forEach(key => {
      const control = this.loginForm.get(key);
      if (control) {
        control.markAsUntouched();
        control.markAsPristine();
      }
    });
  }

  /**
   * Handles successful authentication by managing redirects.
   * Checks if site selection is required and redirects accordingly.
   */
  private handleAuthenticationSuccess(): void {
    this.resetForm();
    
    // Check if site selection is required
    const requiresSiteSelection = this.siteSelectionService.checkSiteSelectionRequired();
    
    if (requiresSiteSelection) {
      // Start site selection workflow if user has access to multiple sites
      this.siteSelectionService.startSiteSelection('/dashboard');
    } else {
      // Navigate directly to dashboard if user has access to only one site
      this.router.navigate(['/dashboard']).catch(error => {
        console.error('Navigation error:', error);
        this.toastService.showError('Error navigating to dashboard');
      });
    }
  }

  /**
   * Handles authentication errors.
   * Logs error details and displays appropriate user-friendly error message.
   * 
   * @param error The authentication error
   * @returns Observable that completes without emitting
   */
  private handleAuthenticationError(error: Error): Observable<never> {
    console.error('Authentication error:', error);
    
    let errorMessage = 'An error occurred during authentication. Please try again.';
    
    // Provide more specific error messages based on error type
    if (error.message) {
      if (error.message.includes('invalid_credentials') || 
          error.message.includes('wrong_credentials')) {
        errorMessage = 'Invalid username or password. Please try again.';
      } else if (error.message.includes('too_many_attempts') || 
                error.message.includes('rate_limit')) {
        errorMessage = 'Too many failed attempts. Please try again later.';
      } else if (error.message.includes('expired')) {
        errorMessage = 'Your session has expired. Please log in again.';
      } else if (error.message.includes('network')) {
        errorMessage = 'Network error. Please check your connection and try again.';
      }
    }
    
    // Display error message to user
    this.toastService.showError(errorMessage);
    
    // Return an observable that completes without emitting
    return of(undefined).pipe(
      tap(() => {}),
      switchMap(() => { throw error; })
    );
  }
}