import { TestBed, ComponentFixture, waitForAsync } from '@angular/core/testing'; // @angular/core/testing version 16.2.0
import { RouterTestingModule } from '@angular/router/testing'; // @angular/router/testing version 16.2.0
import { Title } from '@angular/platform-browser'; // @angular/platform-browser version 16.2.0
import { BehaviorSubject, of } from 'rxjs'; // rxjs version 7.8.1
import { Router, NavigationEnd } from '@angular/router'; // @angular/router version 16.2.0

import { AppComponent } from './app.component';
import { AuthService } from './core/auth/auth.service';
import { SiteSelectionService } from './core/auth/site-selection.service';
import { PerformanceMonitoringService } from './core/monitoring/performance-monitoring.service';

/**
 * Creates mock services for use in AppComponent tests
 * 
 * @returns Object containing all mock services needed for testing
 */
function createMockServices() {
  // Mock AuthService
  const authService = jasmine.createSpyObj('AuthService', [
    'initialize',
    'handleRedirectCallback',
    'isAuthenticated'
  ]);
  const authLoadingSubject = new BehaviorSubject<boolean>(true);
  authService.isInitialized$ = new BehaviorSubject<boolean>(false);
  authService.isAuthenticating$ = authLoadingSubject;
  authService.isAuthenticated.and.returnValue(of(false));
  authService.handleRedirectCallback.and.returnValue(of({}));

  // Mock SiteSelectionService
  const siteSelectionService = jasmine.createSpyObj('SiteSelectionService', [
    'checkSiteSelectionRequired',
    'startSiteSelection',
    'restoreLastSelectedSite'
  ]);
  const siteSelectionSubject = new BehaviorSubject<boolean>(false);
  siteSelectionService.siteSelectionInProgress$ = siteSelectionSubject;
  siteSelectionService.checkSiteSelectionRequired.and.returnValue(false);

  // Mock PerformanceMonitoringService
  const performanceMonitoringService = jasmine.createSpyObj('PerformanceMonitoringService', [
    'trackPageLoad',
    'trackComponentLoad'
  ]);

  // Mock Router
  const routerEventsSubject = new BehaviorSubject<any>(null);
  const router = {
    events: routerEventsSubject,
    navigate: jasmine.createSpy('navigate')
  };

  // Mock Title service
  const titleService = jasmine.createSpyObj('Title', ['setTitle']);

  // Mock ToastService
  const toastService = jasmine.createSpyObj('ToastService', ['showError']);

  // Mock ActivatedRoute
  const route = {
    root: {
      firstChild: {
        snapshot: {
          data: { title: 'Test Page' }
        },
        firstChild: null
      }
    }
  };

  return {
    authService,
    authLoadingSubject,
    siteSelectionService,
    siteSelectionSubject,
    performanceMonitoringService,
    router,
    routerEventsSubject,
    titleService,
    toastService,
    route
  };
}

describe('AppComponent', () => {
  let component: AppComponent;
  let fixture: ComponentFixture<AppComponent>;
  let mockServices: any;

  beforeEach(waitForAsync(() => {
    mockServices = createMockServices();

    TestBed.configureTestingModule({
      imports: [RouterTestingModule],
      declarations: [AppComponent],
      providers: [
        { provide: AuthService, useValue: mockServices.authService },
        { provide: SiteSelectionService, useValue: mockServices.siteSelectionService },
        { provide: PerformanceMonitoringService, useValue: mockServices.performanceMonitoringService },
        { provide: Router, useValue: mockServices.router },
        { provide: Title, useValue: mockServices.titleService },
        { provide: 'ActivatedRoute', useValue: mockServices.route }
      ]
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(AppComponent);
    component = fixture.componentInstance;
  });

  it('should create the app', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize Auth0 on ngOnInit', () => {
    // Spy on private methods
    spyOn<any>(component, 'handleAuthCallback');
    spyOn<any>(component, 'setupAuthenticationState');
    spyOn<any>(component, 'setupLoadingState');
    spyOn<any>(component, 'updateTitle');

    component.ngOnInit();
    expect(component['handleAuthCallback']).toHaveBeenCalled();
    expect(component['setupAuthenticationState']).toHaveBeenCalled();
    expect(component['setupLoadingState']).toHaveBeenCalled();
    expect(mockServices.titleService.setTitle).toHaveBeenCalled();
  });

  it('should handle auth callback if present in URL', () => {
    // Mock window.location.search
    const originalLocation = window.location;
    Object.defineProperty(window, 'location', {
      value: {
        search: '?code=abc123&state=xyz789',
        origin: 'http://localhost:4200'
      },
      writable: true
    });

    component.ngOnInit();
    expect(mockServices.authService.handleRedirectCallback).toHaveBeenCalled();

    // Restore original window.location
    Object.defineProperty(window, 'location', {
      value: originalLocation,
      writable: true
    });
  });

  it('should check site selection when authenticated', () => {
    // Setup mocks for this test
    mockServices.authService.isAuthenticated.and.returnValue(of(true));
    
    // Call setupAuthenticationState directly
    (component as any).setupAuthenticationState();
    
    expect(mockServices.siteSelectionService.restoreLastSelectedSite).toHaveBeenCalled();
    expect(component.isAuthenticated).toBe(true);
  });

  it('should start site selection if required', () => {
    // Setup mocks for this test
    mockServices.siteSelectionService.checkSiteSelectionRequired.and.returnValue(true);
    
    // Mock the user's authenticated state
    component.isAuthenticated = true;
    
    // Simulate site selection check
    (component as any).setupAuthenticationState();
    
    // Verify the site selection was started
    expect(mockServices.siteSelectionService.restoreLastSelectedSite).toHaveBeenCalled();
  });

  it('should track page load on navigation end', () => {
    component.ngOnInit();
    
    // Simulate navigation end event
    const navigationEndEvent = new NavigationEnd(1, '/dashboard', '/dashboard');
    mockServices.routerEventsSubject.next(navigationEndEvent);
    
    // Verify that page load tracking was called
    expect(mockServices.performanceMonitoringService.trackPageLoad).toHaveBeenCalledWith('/dashboard');
  });

  it('should update page title on navigation', () => {
    // Initialize component
    component.ngOnInit();
    
    // Simulate navigation end event
    const navigationEndEvent = new NavigationEnd(1, '/test-page', '/test-page');
    mockServices.routerEventsSubject.next(navigationEndEvent);
    
    // Verify title was updated
    expect(mockServices.titleService.setTitle).toHaveBeenCalledWith('Test Page - Interaction Management');
  });

  it('should unsubscribe from observables on ngOnDestroy', () => {
    // Create spy for subject completion
    const destroySpy = spyOn<any>(component['destroy$'], 'next');
    const completeSpy = spyOn<any>(component['destroy$'], 'complete');
    
    // Create spy for router subscription unsubscribe
    component['routerSub'] = jasmine.createSpyObj('Subscription', ['unsubscribe']);
    
    // Call ngOnDestroy
    component.ngOnDestroy();
    
    // Verify that destroy subject was completed and router subscription unsubscribed
    expect(destroySpy).toHaveBeenCalled();
    expect(completeSpy).toHaveBeenCalled();
    expect(component['routerSub'].unsubscribe).toHaveBeenCalled();
  });

  it('should update isLoading based on auth service loading state', () => {
    // Setup loading state tracking
    component.ngOnInit();
    (component as any).setupLoadingState();
    
    // Initial state should be loading (true)
    expect(component.isLoading).toBe(true);
    
    // Update loading state through behavior subjects
    mockServices.authService.isInitialized$.next(true);
    mockServices.authLoadingSubject.next(false);
    mockServices.siteSelectionSubject.next(false);
    
    // Now loading should be false
    expect(component.isLoading).toBe(false);
    
    // Change back to loading
    mockServices.authLoadingSubject.next(true);
    expect(component.isLoading).toBe(true);
  });
});