import { Component, OnInit, OnDestroy } from '@angular/core';
import { FormGroup } from '@angular/forms';
import { Subscription } from 'rxjs';
import { take } from 'rxjs/operators';

import { AuthService } from '../../../../core/auth/auth.service';
import { AuthPageService } from '../../services/auth-page.service';
import { ErrorHandlerService } from '../../../../core/errors/error-handler.service';

/**
 * Component that renders the login form and handles user authentication interactions.
 * Implements the login screen interface defined in the technical specifications,
 * providing form validation, error handling, and authentication flow.
 */
@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss']
})
export class LoginComponent implements OnInit, OnDestroy {
  /** Reactive form for login credentials */
  loginForm: FormGroup;
  
  /** Flag indicating if form is currently submitting */
  isSubmitting: boolean = false;
  
  /** Record of validation errors keyed by form control name */
  formErrors: Record<string, string[]> = {};
  
  /** Flag indicating if authentication is in progress */
  isAuthenticating: boolean = false;
  
  /** Remember me checkbox state */
  rememberMe: boolean = false;
  
  /** Subscription collection for cleanup */
  private subscription: Subscription = new Subscription();

  /**
   * Creates an instance of LoginComponent
   * 
   * @param authService Service handling authentication operations
   * @param authPageService Service managing login form state and submission
   * @param errorHandler Service for handling authentication errors
   */
  constructor(
    private authService: AuthService,
    private authPageService: AuthPageService,
    private errorHandler: ErrorHandlerService
  ) {}

  /**
   * Lifecycle hook that initializes component state after Angular has
   * initialized all data-bound properties
   */
  ngOnInit(): void {
    // Get login form reference from auth page service
    this.loginForm = this.authPageService.loginForm;
    
    // Subscribe to form submission state
    this.subscription.add(
      this.authPageService.isSubmitting$.subscribe(
        isSubmitting => this.isSubmitting = isSubmitting
      )
    );
    
    // Subscribe to form validation errors
    this.subscription.add(
      this.authPageService.formErrors$.subscribe(
        errors => this.formErrors = errors
      )
    );
    
    // Subscribe to authentication state
    this.subscription.add(
      this.authService.isAuthenticating$.subscribe(
        isAuthenticating => this.isAuthenticating = isAuthenticating
      )
    );
  }

  /**
   * Lifecycle hook that cleans up subscriptions when component is destroyed
   */
  ngOnDestroy(): void {
    // Unsubscribe from all subscriptions to prevent memory leaks
    this.subscription.unsubscribe();
  }

  /**
   * Handles login form submission
   */
  onSubmit(): void {
    // Prevent submission if already in progress
    if (this.isSubmitting || this.isAuthenticating) {
      return;
    }
    
    // Process login via auth page service
    this.authPageService.handleLoginSubmit()
      .pipe(take(1)) // Take only first result and complete
      .subscribe({
        error: (error) => {
          // Handle authentication error
          this.errorHandler.handleError(error, 'LoginComponent.onSubmit');
        }
      });
  }

  /**
   * Handles forgot password link click
   */
  onForgotPassword(): void {
    try {
      this.authPageService.handleForgotPassword();
    } catch (error) {
      this.errorHandler.handleError(error, 'LoginComponent.onForgotPassword');
    }
  }

  /**
   * Toggles the remember me checkbox value
   */
  toggleRememberMe(): void {
    this.rememberMe = !this.rememberMe;
    
    // Update form control value
    const rememberMeControl = this.loginForm.get('rememberMe');
    if (rememberMeControl) {
      rememberMeControl.setValue(this.rememberMe);
    }
  }

  /**
   * Checks if a specific form control has errors
   * 
   * @param controlName Name of the form control to check
   * @returns True if the control has errors and has been touched
   */
  hasError(controlName: string): boolean {
    return (
      !!this.formErrors[controlName] && 
      this.formErrors[controlName].length > 0 && 
      !!this.loginForm.get(controlName)?.touched
    );
  }

  /**
   * Gets error messages for a specific form control
   * 
   * @param controlName Name of the form control
   * @returns Array of error messages for the control
   */
  getErrorMessages(controlName: string): string[] {
    return this.authPageService.getFormControlErrors(controlName);
  }
}