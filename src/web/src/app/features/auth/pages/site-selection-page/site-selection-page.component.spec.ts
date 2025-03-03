import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing'; // @angular/core/testing 16.2.0
import { NO_ERRORS_SCHEMA } from '@angular/core'; // @angular/core 16.2.0
import { Router } from '@angular/router'; // @angular/router 16.2.0
import { BehaviorSubject, of } from 'rxjs'; // rxjs 7.8.1

import { SiteSelectionPageComponent } from './site-selection-page.component';
import { SiteSelectionComponent } from '../../components/site-selection/site-selection.component';
import { SiteSelectionService } from '../../../../core/auth/site-selection.service';
import { UserContextService } from '../../../../core/auth/user-context.service';
import { SiteWithRole } from '../../../../features/sites/models/site.model';

describe('SiteSelectionPageComponent', () => {
  let component: SiteSelectionPageComponent;
  let fixture: ComponentFixture<SiteSelectionPageComponent>;
  let mockRouter: jasmine.SpyObj<Router>;
  let mockSiteSelectionService: jasmine.SpyObj<SiteSelectionService>;
  let mockUserContextService: jasmine.SpyObj<UserContextService>;
  let loadingSubject: BehaviorSubject<boolean>;
  let mockUser: any;

  beforeEach(waitForAsync(() => {
    // Create mock services
    mockRouter = jasmine.createSpyObj('Router', ['navigate']);
    mockSiteSelectionService = jasmine.createSpyObj('SiteSelectionService', [
      'getRedirectUrl',
      'siteSelectionInProgress$'
    ]);
    mockUserContextService = jasmine.createSpyObj('UserContextService', ['getCurrentUser']);

    // Create BehaviorSubject for the loading state
    loadingSubject = new BehaviorSubject<boolean>(false);
    mockSiteSelectionService.siteSelectionInProgress$ = loadingSubject.asObservable();

    // Setup mockUserContextService to return mockUser
    mockUser = {
      id: 'user1',
      username: 'testuser',
      email: 'test@example.com',
      sites: [
        { id: 1, name: 'Headquarters', role: 'admin' },
        { id: 2, name: 'Northwest Regional Office', role: 'editor' }
      ],
      currentSiteId: null,
      isAuthenticated: true
    };
    mockUserContextService.getCurrentUser.and.returnValue(mockUser);
    
    // Configure mockSiteSelectionService.getRedirectUrl to return dashboard path
    mockSiteSelectionService.getRedirectUrl.and.returnValue('/dashboard');

    // Configure TestBed with necessary providers and components
    TestBed.configureTestingModule({
      declarations: [SiteSelectionPageComponent],
      providers: [
        { provide: Router, useValue: mockRouter },
        { provide: SiteSelectionService, useValue: mockSiteSelectionService },
        { provide: UserContextService, useValue: mockUserContextService }
      ],
      schemas: [NO_ERRORS_SCHEMA] // Ignore unknown elements in tests
    }).compileComponents();
  }));

  beforeEach(() => {
    // Create component fixture
    fixture = TestBed.createComponent(SiteSelectionPageComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should check authentication status on init', () => {
    // Verify mockUserContextService.getCurrentUser was called
    expect(mockUserContextService.getCurrentUser).toHaveBeenCalled();
    expect(component).toBeTruthy();
  });

  it('should redirect unauthenticated user to login', () => {
    // Set mockUserContextService.getCurrentUser to return null
    mockUserContextService.getCurrentUser.and.returnValue(null);
    component.ngOnInit();
    // Verify redirection to login page
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/auth/login']);
  });

  it('should handle loading state from service', () => {
    // Emit true from loadingSubject
    loadingSubject.next(true);
    expect(component.isLoading).toBeTrue();
    
    // Emit false from loadingSubject
    loadingSubject.next(false);
    expect(component.isLoading).toBeFalse();
  });

  it('should clean up subscriptions on destruction', () => {
    // Create spy on subscription.unsubscribe
    spyOn(component.subscription, 'unsubscribe');
    
    // Call ngOnDestroy
    component.ngOnDestroy();
    
    // Expect unsubscribe to have been called
    expect(component.subscription.unsubscribe).toHaveBeenCalled();
  });

  it('should handle site selection', () => {
    // Call onSiteSelected method
    component.onSiteSelected();
    
    // Verify navigation to dashboard
    expect(mockSiteSelectionService.getRedirectUrl).toHaveBeenCalled();
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/dashboard']);
  });

  it('should handle cancel selection', () => {
    // Call onCancelSelection method
    component.onCancelSelection();
    
    // Verify redirection to login page
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/auth/login']);
  });
});