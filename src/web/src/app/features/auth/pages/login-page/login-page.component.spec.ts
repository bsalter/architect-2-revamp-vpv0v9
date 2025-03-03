import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { Router, ActivatedRoute } from '@angular/router';
import { By } from '@angular/platform-browser';
import { of, Subject, BehaviorSubject } from 'rxjs';
import { NO_ERRORS_SCHEMA } from '@angular/core';

import { LoginPageComponent } from './login-page.component';
import { LoginComponent } from '../../components/login/login.component';
import { AuthService } from '../../../../core/auth/auth.service';
import { SiteSelectionService } from '../../../../core/auth/site-selection.service';
import { AuthPageService } from '../../services/auth-page.service';
import { ToastService } from '../../../../shared/services/toast.service';

describe('LoginPageComponent', () => {
  let fixture: ComponentFixture<LoginPageComponent>;
  let component: LoginPageComponent;
  let authServiceMock: any;
  let siteSelectionServiceMock: any;
  let authPageServiceMock: any;
  let toastServiceMock: any;
  let routerMock: any;
  let activatedRouteMock: any;
  
  // Subjects to control test data flow
  let isInitializedSubject: BehaviorSubject<boolean>;
  let authCallbackSubject: Subject<boolean>;

  beforeEach(waitForAsync(() => {
    // Initialize subjects
    isInitializedSubject = new BehaviorSubject<boolean>(false);
    authCallbackSubject = new Subject<boolean>();
    
    // Create mock services
    authServiceMock = {
      isInitialized$: isInitializedSubject.asObservable(),
      isAuthenticated: jasmine.createSpy('isAuthenticated').and.returnValue(of(false))
    };
    
    authPageServiceMock = {
      checkAndHandleAuthRedirect: jasmine.createSpy('checkAndHandleAuthRedirect').and.returnValue(authCallbackSubject.asObservable())
    };
    
    siteSelectionServiceMock = {
      checkSiteSelectionRequired: jasmine.createSpy('checkSiteSelectionRequired').and.returnValue(false),
      startSiteSelection: jasmine.createSpy('startSiteSelection')
    };
    
    toastServiceMock = {
      showError: jasmine.createSpy('showError')
    };
    
    routerMock = {
      navigate: jasmine.createSpy('navigate'),
      navigateByUrl: jasmine.createSpy('navigateByUrl')
    };
    
    activatedRouteMock = {
      snapshot: {
        queryParams: { returnUrl: '/dashboard' }
      }
    };

    // Configure TestBed
    TestBed.configureTestingModule({
      declarations: [LoginPageComponent],
      providers: [
        { provide: AuthService, useValue: authServiceMock },
        { provide: AuthPageService, useValue: authPageServiceMock },
        { provide: SiteSelectionService, useValue: siteSelectionServiceMock },
        { provide: ToastService, useValue: toastServiceMock },
        { provide: Router, useValue: routerMock },
        { provide: ActivatedRoute, useValue: activatedRouteMock }
      ],
      schemas: [NO_ERRORS_SCHEMA] // Ignore unknown elements
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(LoginPageComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create the component', () => {
    expect(component).toBeTruthy();
  });

  it('should show loading state when isLoading is true', () => {
    component.isLoading = true;
    fixture.detectChanges();
    
    // Check for loading indicator - adjust based on actual template
    const loadingElement = fixture.debugElement.query(By.css('.loading-indicator'));
    expect(loadingElement).toBeTruthy();
  });

  it('should check for authentication callback parameters', () => {
    // Trigger Auth0 initialization
    isInitializedSubject.next(true);
    fixture.detectChanges();
    
    // Verify callback check was performed
    expect(authPageServiceMock.checkAndHandleAuthRedirect).toHaveBeenCalled();
  });

  it('should redirect to finder page when user is authenticated and site selection not required', () => {
    // Setup test conditions
    authServiceMock.isAuthenticated.and.returnValue(of(true));
    siteSelectionServiceMock.checkSiteSelectionRequired.and.returnValue(false);
    
    // Trigger auth flow
    isInitializedSubject.next(true);
    authCallbackSubject.next(false); // No callback handling
    
    // Wait for async operations
    fixture.whenStable().then(() => {
      // Verify navigation
      expect(routerMock.navigateByUrl).toHaveBeenCalledWith('/dashboard');
    });
  });

  it('should redirect to site selection when user is authenticated and site selection is required', () => {
    // Setup test conditions
    authServiceMock.isAuthenticated.and.returnValue(of(true));
    siteSelectionServiceMock.checkSiteSelectionRequired.and.returnValue(true);
    
    // Trigger auth flow
    isInitializedSubject.next(true);
    authCallbackSubject.next(false); // No callback handling
    
    // Wait for async operations
    fixture.whenStable().then(() => {
      // Verify site selection was started
      expect(siteSelectionServiceMock.startSiteSelection).toHaveBeenCalledWith('/dashboard');
    });
  });

  it('should unsubscribe from observables on component destruction', () => {
    // Create spies on destroy$ Subject
    spyOn(component['destroy$'], 'next');
    spyOn(component['destroy$'], 'complete');
    
    // Trigger ngOnDestroy
    component.ngOnDestroy();
    
    // Verify unsubscription
    expect(component['destroy$'].next).toHaveBeenCalled();
    expect(component['destroy$'].complete).toHaveBeenCalled();
  });
});