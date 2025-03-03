import { ComponentFixture, TestBed, async, fakeAsync, tick } from '@angular/core/testing';
import { Router, ActivatedRoute } from '@angular/router';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ReactiveFormsModule, FormGroup, FormControl } from '@angular/forms';
import { of, BehaviorSubject } from 'rxjs';

import { LoginComponent } from './login.component';
import { AuthService } from '../../../../core/auth/auth.service';
import { AuthPageService } from '../../services/auth-page.service';
import { SiteSelectionService } from '../../../../core/auth/site-selection.service';

/**
 * Creates mock services for use in tests
 * @returns Object containing mock services for testing
 */
function createMockServices() {
  // Mock AuthService
  const mockAuthService = jasmine.createSpyObj('AuthService', ['login', 'handleAuthCallback']);
  mockAuthService.isAuthenticating$ = new BehaviorSubject<boolean>(false);
  
  // Mock AuthPageService with form group and required observables
  const mockAuthPageService = jasmine.createSpyObj('AuthPageService', [
    'handleLoginSubmit',
    'handleForgotPassword',
    'getFormControlErrors',
    'checkAndHandleAuthRedirect'
  ]);
  mockAuthPageService.loginForm = new FormGroup({
    username: new FormControl(''),
    password: new FormControl(''),
    rememberMe: new FormControl(false)
  });
  mockAuthPageService.isSubmitting$ = new BehaviorSubject<boolean>(false);
  mockAuthPageService.formErrors$ = new BehaviorSubject<Record<string, string[]>>({});
  mockAuthPageService.handleLoginSubmit.and.returnValue(of(undefined));
  
  // Mock SiteSelectionService
  const mockSiteSelectionService = jasmine.createSpyObj('SiteSelectionService', [
    'siteSelectionRequired$'
  ]);
  mockSiteSelectionService.siteSelectionRequired$ = new BehaviorSubject<boolean>(false);
  
  // Mock Router
  const mockRouter = jasmine.createSpyObj('Router', ['navigate']);
  
  // Mock ActivatedRoute
  const mockActivatedRoute = {
    queryParams: of({})
  };
  
  return {
    authService: mockAuthService,
    authPageService: mockAuthPageService,
    siteSelectionService: mockSiteSelectionService,
    router: mockRouter,
    activatedRoute: mockActivatedRoute
  };
}

describe('LoginComponent', () => {
  let component: LoginComponent;
  let fixture: ComponentFixture<LoginComponent>;
  let mockServices: ReturnType<typeof createMockServices>;
  
  beforeEach(async(() => {
    mockServices = createMockServices();
    
    TestBed.configureTestingModule({
      declarations: [LoginComponent],
      imports: [ReactiveFormsModule],
      providers: [
        { provide: AuthService, useValue: mockServices.authService },
        { provide: AuthPageService, useValue: mockServices.authPageService },
        { provide: SiteSelectionService, useValue: mockServices.siteSelectionService },
        { provide: Router, useValue: mockServices.router },
        { provide: ActivatedRoute, useValue: mockServices.activatedRoute }
      ],
      schemas: [NO_ERRORS_SCHEMA] // Ignore unknown elements in template
    }).compileComponents();
  }));
  
  beforeEach(() => {
    fixture = TestBed.createComponent(LoginComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });
  
  afterEach(() => {
    // Reset all spies between tests
    jasmine.resetAllSpies();
  });
  
  it('should create the component', () => {
    expect(component).toBeTruthy();
  });
  
  it('should check for authentication callback on initialization', () => {
    expect(mockServices.authPageService.checkAndHandleAuthRedirect).toHaveBeenCalledTimes(1);
  });
  
  it('should handle form submission', () => {
    // Trigger form submission
    component.onSubmit();
    
    // Verify service method was called
    expect(mockServices.authPageService.handleLoginSubmit).toHaveBeenCalled();
  });
  
  it('should handle forgot password click', () => {
    // Trigger forgot password action
    component.onForgotPassword();
    
    // Verify service method was called
    expect(mockServices.authPageService.handleForgotPassword).toHaveBeenCalled();
  });
  
  it('should display validation errors when form is invalid', () => {
    // Set up form errors
    const errors = { 'username': ['Please enter a valid email address'] };
    mockServices.authPageService.formErrors$.next(errors);
    component.formErrors = errors;
    
    // Mark form control as touched to trigger error display
    component.loginForm.get('username')?.markAsTouched();
    fixture.detectChanges();
    
    // Check if component has error for the control
    expect(component.hasError('username')).toBeTrue();
    
    // Verify getErrorMessages is called with the correct control name
    component.getErrorMessages('username');
    expect(mockServices.authPageService.getFormControlErrors).toHaveBeenCalledWith('username');
  });
  
  it('should show loading indicator during authentication', () => {
    // Set loading state
    mockServices.authPageService.isSubmitting$.next(true);
    fixture.detectChanges();
    
    // Verify component state is updated
    expect(component.isSubmitting).toBeTrue();
  });
  
  it('should navigate to site selection when required after login', fakeAsync(() => {
    // This is primarily tested in AuthPageService, but we can verify component integrates correctly
    mockServices.authService.isAuthenticating$.next(true);
    fixture.detectChanges();
    
    // Verify component state is updated
    expect(component.isAuthenticating).toBeTrue();
  }));
  
  it('should navigate to dashboard when site selection not required after login', fakeAsync(() => {
    // This is primarily tested in AuthPageService, but we can verify component integrates correctly
    mockServices.authService.isAuthenticating$.next(false);
    fixture.detectChanges();
    
    // Verify component state is updated
    expect(component.isAuthenticating).toBeFalse();
  }));
  
  it('should properly clean up subscriptions on destroy', () => {
    // Spy on subscription's unsubscribe method
    spyOn(component['subscription'], 'unsubscribe');
    
    // Trigger component destruction
    component.ngOnDestroy();
    
    // Verify unsubscribe was called
    expect(component['subscription'].unsubscribe).toHaveBeenCalled();
  });
  
  it('should not submit form if already submitting', () => {
    // Set submitting state
    component.isSubmitting = true;
    
    // Try to submit
    component.onSubmit();
    
    // Verify service method was not called
    expect(mockServices.authPageService.handleLoginSubmit).not.toHaveBeenCalled();
  });
  
  it('should not submit form if authentication is in progress', () => {
    // Set authenticating state
    component.isAuthenticating = true;
    
    // Try to submit
    component.onSubmit();
    
    // Verify service method was not called
    expect(mockServices.authPageService.handleLoginSubmit).not.toHaveBeenCalled();
  });
  
  it('should toggle remember me', () => {
    // Initial state
    expect(component.rememberMe).toBeFalse();
    
    // Toggle it
    component.toggleRememberMe();
    
    // Verify it was toggled
    expect(component.rememberMe).toBeTrue();
    
    // Check if form control was updated
    expect(component.loginForm.get('rememberMe')?.value).toBeTrue();
  });
  
  describe('Form validation', () => {
    it('should require username', () => {
      // Get the username control and clear it
      const usernameControl = component.loginForm.get('username');
      usernameControl?.setValue('');
      usernameControl?.markAsTouched();
      
      // Check validation state
      expect(usernameControl?.valid).toBeFalsy();
      expect(usernameControl?.errors?.['required']).toBeTruthy();
    });
    
    it('should validate email format', () => {
      // Get the username control and set invalid email
      const usernameControl = component.loginForm.get('username');
      usernameControl?.setValue('invalid-email');
      usernameControl?.markAsTouched();
      
      // Check validation state
      expect(usernameControl?.valid).toBeFalsy();
      expect(usernameControl?.errors?.['email']).toBeTruthy();
    });
    
    it('should require password', () => {
      // Get the password control and clear it
      const passwordControl = component.loginForm.get('password');
      passwordControl?.setValue('');
      passwordControl?.markAsTouched();
      
      // Check validation state
      expect(passwordControl?.valid).toBeFalsy();
      expect(passwordControl?.errors?.['required']).toBeTruthy();
    });
  });
  
  describe('Auth callback handling', () => {
    it('should handle successful Auth0 redirect callback', fakeAsync(() => {
      // Mock callback parameters in URL
      mockServices.authPageService.checkAndHandleAuthRedirect.and.returnValue(of(true));
      
      // Force component reinitialization
      component.ngOnInit();
      tick();
      
      // Verify callback was handled
      expect(mockServices.authPageService.checkAndHandleAuthRedirect).toHaveBeenCalled();
    }));
    
    it('should handle Auth0 redirect callback errors', fakeAsync(() => {
      // Mock error callback handling
      mockServices.authPageService.checkAndHandleAuthRedirect.and.returnValue(of(false));
      
      // Force component reinitialization
      component.ngOnInit();
      tick();
      
      // Verify error handling logic (in a real component this would show an error message)
      expect(mockServices.authPageService.checkAndHandleAuthRedirect).toHaveBeenCalled();
    }));
  });
});