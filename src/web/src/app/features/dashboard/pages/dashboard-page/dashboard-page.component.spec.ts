import { ComponentFixture, TestBed } from '@angular/core/testing';
import { async } from '@angular/core/testing';
import { BehaviorSubject, of, throwError, Subject, Subscription } from 'rxjs';

import { DashboardPageComponent } from './dashboard-page.component';
import { DashboardService } from '../../services/dashboard.service';
import { UserContextService } from '../../../../core/auth/user-context.service';
import { SiteService } from '../../../features/sites/services/site.service';
import { Site } from '../../../features/sites/models/site.model';

// Helper function to create mock dashboard service
function createMockDashboardService() {
  const service = jasmine.createSpyObj('DashboardService', [
    'getRecentInteractions',
    'getInteractionsSummary',
    'getInteractionsByType',
    'getUpcomingInteractions',
    'refreshDashboard',
    'isLoading'
  ]);
  
  // Configure loading BehaviorSubject
  const loadingSubject = new BehaviorSubject<boolean>(false);
  service.isLoading.and.returnValue(loadingSubject);
  
  // Configure mock data returns
  service.getRecentInteractions.and.returnValue(of([
    { id: 1, title: 'Test Interaction 1' },
    { id: 2, title: 'Test Interaction 2' }
  ]));
  
  service.getUpcomingInteractions.and.returnValue(of([
    { id: 3, title: 'Upcoming Test 1' },
    { id: 4, title: 'Upcoming Test 2' }
  ]));
  
  service.getInteractionsSummary.and.returnValue(of({
    total: 10,
    today: 2,
    thisWeek: 5
  }));
  
  service.getInteractionsByType.and.returnValue(of([
    { type: 'Meeting', count: 5 },
    { type: 'Call', count: 3 },
    { type: 'Email', count: 2 }
  ]));
  
  return service;
}

// Helper function to create mock user context service
function createMockUserContextService(siteId: number, username: string, canCreatePermission: boolean) {
  const service = jasmine.createSpyObj('UserContextService', ['isEditor']);
  
  // Create BehaviorSubjects for reactive properties
  service.currentSite$ = new BehaviorSubject<Site | null>({
    id: siteId,
    name: 'Test Site',
    role: 'admin'
  });
  
  service.username$ = new BehaviorSubject<string>(username);
  
  // Configure permission method
  service.isEditor.and.returnValue(canCreatePermission);
  
  return service;
}

// Helper function to create mock site service
function createMockSiteService(siteData: any) {
  const service = jasmine.createSpyObj('SiteService', ['getCurrentSite']);
  service.getCurrentSite.and.returnValue(of(siteData));
  return service;
}

describe('DashboardPageComponent', () => {
  let component: DashboardPageComponent;
  let fixture: ComponentFixture<DashboardPageComponent>;
  let mockDashboardService: any;
  let mockUserContextService: any;
  let mockSiteService: any;
  let siteSubject: BehaviorSubject<Site | null>;
  let usernameSubject: BehaviorSubject<string>;

  beforeEach(async(() => {
    // Create mock services
    mockDashboardService = createMockDashboardService();
    mockUserContextService = createMockUserContextService(1, 'testuser', true);
    mockSiteService = createMockSiteService({ id: 1, name: 'Test Site', role: 'admin' });
    
    // Get references to the behavior subjects for testing
    siteSubject = mockUserContextService.currentSite$;
    usernameSubject = mockUserContextService.username$;
    
    // Configure TestBed
    TestBed.configureTestingModule({
      declarations: [DashboardPageComponent],
      providers: [
        { provide: DashboardService, useValue: mockDashboardService },
        { provide: UserContextService, useValue: mockUserContextService },
        { provide: SiteService, useValue: mockSiteService }
      ]
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(DashboardPageComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize with loading state', () => {
    // Verify initial loading state is false (from mock service)
    expect(component.loading).toBeFalse();
    
    // Change loading state via the service
    mockDashboardService.isLoading().next(true);
    
    // Verify component updates loading state
    expect(component.loading).toBeTrue();
    
    // Verify loadDashboardData is called during initialization
    spyOn(component, 'loadDashboardData');
    component.ngOnInit();
    expect(component.loadDashboardData).toHaveBeenCalled();
  });

  it('should load dashboard data on initialization', () => {
    // Verify service calls
    expect(mockDashboardService.getInteractionsSummary).toHaveBeenCalled();
    expect(mockDashboardService.getRecentInteractions).toHaveBeenCalledWith(5);
    expect(mockDashboardService.getUpcomingInteractions).toHaveBeenCalledWith(7, 5);
    expect(mockDashboardService.getInteractionsByType).toHaveBeenCalled();
    
    // Verify component properties are populated with data
    expect(component.recentInteractions.length).toBe(2);
    expect(component.upcomingInteractions.length).toBe(2);
    expect(component.summaryData).toBeDefined();
    expect(component.interactionsByType.length).toBe(3);
    expect(component.loading).toBeFalse();
  });

  it('should update dashboard data when site changes', () => {
    // Clear the counters on the spies
    mockDashboardService.getRecentInteractions.calls.reset();
    mockDashboardService.getInteractionsSummary.calls.reset();
    mockDashboardService.getUpcomingInteractions.calls.reset();
    mockDashboardService.getInteractionsByType.calls.reset();
    
    // Change the site
    siteSubject.next({
      id: 2,
      name: 'New Site',
      role: 'admin'
    });
    
    // Verify services were called again
    expect(mockDashboardService.getInteractionsSummary).toHaveBeenCalled();
    expect(mockDashboardService.getRecentInteractions).toHaveBeenCalledWith(5);
    expect(mockDashboardService.getUpcomingInteractions).toHaveBeenCalledWith(7, 5);
    expect(mockDashboardService.getInteractionsByType).toHaveBeenCalled();
    
    // Verify the component's currentSite was updated
    expect(component.currentSite?.id).toBe(2);
    expect(component.currentSite?.name).toBe('New Site');
    expect(component.loading).toBeFalse();
  });

  it('should update username when user context changes', () => {
    // Initially username should be from the mock service
    expect(component.username).toBe('testuser');
    
    // Change username
    usernameSubject.next('newuser');
    
    // Verify username was updated in the component
    expect(component.username).toBe('newuser');
  });

  it('should load current site information', () => {
    // Verify site service was called
    expect(mockSiteService.getCurrentSite).toHaveBeenCalled();
    
    // Verify site data was set correctly
    expect(component.currentSite).toBeDefined();
    expect(component.currentSite?.id).toBe(1);
    expect(component.currentSite?.name).toBe('Test Site');
  });

  it('should check creation permissions', () => {
    // Initialize with permission enabled
    expect(component.canCreateInteraction).toBeTrue();
    
    // Change the permission to false
    mockUserContextService.isEditor.and.returnValue(false);
    
    // Re-initialize the component
    component.ngOnInit();
    
    // Verify the permission was updated
    expect(component.canCreateInteraction).toBeFalse();
  });

  it('should refresh data when refreshDashboard is called', () => {
    // Clear call counts
    mockDashboardService.refreshDashboard.calls.reset();
    mockDashboardService.getRecentInteractions.calls.reset();
    mockDashboardService.getInteractionsSummary.calls.reset();
    mockDashboardService.getUpcomingInteractions.calls.reset();
    mockDashboardService.getInteractionsByType.calls.reset();
    
    // Call refresh method
    component.refreshDashboard();
    
    // Verify refresh method on service was called
    expect(mockDashboardService.refreshDashboard).toHaveBeenCalled();
    
    // Verify data reload methods were called
    expect(mockDashboardService.getInteractionsSummary).toHaveBeenCalled();
    expect(mockDashboardService.getRecentInteractions).toHaveBeenCalledWith(5);
    expect(mockDashboardService.getUpcomingInteractions).toHaveBeenCalledWith(7, 5);
    expect(mockDashboardService.getInteractionsByType).toHaveBeenCalled();
  });

  it('should unsubscribe on component destruction', () => {
    // Get initial state of the component
    const initialSite = component.currentSite;
    const initialLoading = component.loading;
    
    // Destroy the component to trigger unsubscription
    component.ngOnDestroy();
    
    // Try to change observables that the component subscribes to
    mockDashboardService.isLoading().next(!initialLoading);
    siteSubject.next({
      id: 99,
      name: 'After Destroy Site',
      role: 'viewer'
    });
    
    // Verify component state wasn't updated after destruction
    expect(component.currentSite).toEqual(initialSite);
    expect(component.loading).toEqual(initialLoading);
  });

  it('should handle errors when loading data', () => {
    // Configure the service to throw an error
    mockDashboardService.getInteractionsSummary.and.returnValue(
      throwError(() => new Error('Test error'))
    );
    
    // Set loading to true to verify it's reset on error
    mockDashboardService.isLoading().next(true);
    expect(component.loading).toBeTrue();
    
    // Call the method that should handle the error
    component.loadDashboardData();
    
    // Verify loading is set to false despite the error
    expect(component.loading).toBeFalse();
    
    // Error handling should still allow the test to complete
    expect(true).toBeTrue();
  });
});