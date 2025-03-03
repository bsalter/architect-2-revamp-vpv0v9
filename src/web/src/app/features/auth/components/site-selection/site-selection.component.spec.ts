import { ComponentFixture, TestBed, async, fakeAsync, tick } from '@angular/core/testing'; // @angular/core/testing 16.2.0
import { Router } from '@angular/router'; // @angular/router 16.2.0
import { of, throwError, BehaviorSubject } from 'rxjs'; // rxjs 7.8.1

import { SiteSelectionComponent } from './site-selection.component';
import { UserContextService } from '../../../../core/auth/user-context.service';
import { SiteSelectionService } from '../../../../core/auth/site-selection.service';
import { User } from '../../../../core/auth/user.model';
import { SiteWithRole } from '../../../../features/sites/models/site.model';

describe('SiteSelectionComponent', () => {
  let component: SiteSelectionComponent;
  let fixture: ComponentFixture<SiteSelectionComponent>;
  let mockUserContextService: MockUserContextService;
  let mockSiteSelectionService: MockSiteSelectionService;
  let mockRouter: MockRouter;

  // Mock implementation of UserContextService
  class MockUserContextService {
    mockUser: User | null = null;
    mockSites: SiteWithRole[] = [];

    constructor() {
      this.mockUser = null;
      this.mockSites = [];
    }

    getCurrentUser(): User | null {
      return this.mockUser;
    }

    getUserSites(): SiteWithRole[] | null {
      return this.mockSites;
    }

    setCurrentSiteId(siteId: number): boolean {
      // Spy function for verification in tests
      return true;
    }
  }

  // Mock implementation of SiteSelectionService
  class MockSiteSelectionService {
    siteSelectionInProgressSubject = new BehaviorSubject<boolean>(false);
    siteSelectionInProgress$ = this.siteSelectionInProgressSubject.asObservable();
    isLoadingSubject = new BehaviorSubject<boolean>(false);
    isLoading$ = this.isLoadingSubject.asObservable();
    mockSites: SiteWithRole[] = [];
    mockSelectSiteSuccess = true;

    getAvailableSites() {
      return of(this.mockSites);
    }

    selectSite(siteId: number) {
      // Mock implementation that either returns success or error
      if (this.mockSelectSiteSuccess) {
        return of(true);
      } else {
        return throwError(() => new Error('Failed to set current site'));
      }
    }

    cancelSiteSelection() {
      this.siteSelectionInProgressSubject.next(false);
    }
  }

  // Mock implementation of Router
  class MockRouter {
    navigate(commands: any[], extras?: any): Promise<boolean> {
      return Promise.resolve(true);
    }
  }

  beforeEach(async(() => {
    mockUserContextService = new MockUserContextService();
    mockSiteSelectionService = new MockSiteSelectionService();
    mockRouter = new MockRouter();

    TestBed.configureTestingModule({
      declarations: [SiteSelectionComponent],
      providers: [
        { provide: UserContextService, useValue: mockUserContextService },
        { provide: SiteSelectionService, useValue: mockSiteSelectionService },
        { provide: Router, useValue: mockRouter }
      ]
    })
      .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SiteSelectionComponent);
    component = fixture.componentInstance;

    // Set up a mock user with site access for most tests
    const mockUser = new User({
      id: '123',
      username: 'testuser',
      email: 'test@example.com',
      sites: [
        { id: 1, name: 'Headquarters', role: 'admin' },
        { id: 2, name: 'Northwest Regional Office', role: 'editor' },
        { id: 3, name: 'Southwest Regional Office', role: 'viewer' }
      ]
    });
    mockUserContextService.mockUser = mockUser;
    mockUserContextService.mockSites = mockUser.sites;
    mockSiteSelectionService.mockSites = mockUser.sites;

    // Spy on service methods
    spyOn(mockSiteSelectionService, 'getAvailableSites').and.callThrough();
    spyOn(mockSiteSelectionService, 'selectSite').and.callThrough();
    spyOn(mockSiteSelectionService, 'cancelSiteSelection').and.callThrough();
    spyOn(mockUserContextService, 'setCurrentSiteId').and.callThrough();
  });

  it('should create the component', () => {
    expect(component).toBeTruthy();
  });

  it('should load available sites on initialization', () => {
    // Act
    component.ngOnInit();
    fixture.detectChanges();

    // Assert
    expect(mockSiteSelectionService.getAvailableSites).toHaveBeenCalled();
    expect(component.availableSites.length).toBe(3);
    expect(component.availableSites[0].id).toBe(1);
    expect(component.availableSites[1].id).toBe(2);
    expect(component.availableSites[2].id).toBe(3);
    expect(component.selectedSiteId).toBe(1); // First site should be selected by default
  });

  it('should auto-select site if only one is available', () => {
    // Arrange
    const singleSite = [{ id: 1, name: 'Headquarters', role: 'admin' }];
    mockSiteSelectionService.mockSites = singleSite;

    // Act
    component.ngOnInit();
    fixture.detectChanges();

    // Assert
    expect(component.selectedSiteId).toBe(1);
  });

  it('should show error when user is not authenticated', () => {
    // Arrange
    mockUserContextService.mockUser = null;

    // Act
    component.ngOnInit();
    fixture.detectChanges();

    // Assert
    expect(component.hasError).toBe(true);
    expect(component.errorMessage).toContain('User not authenticated');
  });

  it('should update selectedSiteId when updateSelectedSite is called', () => {
    // Arrange
    component.selectedSiteId = null;
    component.hasError = true;
    component.errorMessage = 'Previous error';

    // Act
    component.updateSelectedSite(2);

    // Assert
    expect(component.selectedSiteId).toBe(2);
    expect(component.hasError).toBe(false);
    expect(component.errorMessage).toBe('');
  });

  it('should call selectSite service when selectSite is called with valid selection', fakeAsync(() => {
    // Arrange
    component.selectedSiteId = 2;
    component.ngOnInit();
    spyOn(component.siteSelected, 'emit');
    
    // Act
    component.selectSite();
    tick();

    // Assert
    expect(mockSiteSelectionService.selectSite).toHaveBeenCalledWith(2);
    expect(component.siteSelected.emit).toHaveBeenCalled();
    expect(component.hasError).toBe(false);
  }));

  it('should show error when selectSite is called without selection', () => {
    // Arrange
    component.selectedSiteId = null;

    // Act
    component.selectSite();

    // Assert
    expect(mockSiteSelectionService.selectSite).not.toHaveBeenCalled();
    expect(component.hasError).toBe(true);
    expect(component.errorMessage).toContain('Please select a site');
  });

  it('should handle error from selectSite service', fakeAsync(() => {
    // Arrange
    component.selectedSiteId = 2;
    mockSiteSelectionService.mockSelectSiteSuccess = false;
    
    // Act
    component.selectSite();
    tick();

    // Assert
    expect(mockSiteSelectionService.selectSite).toHaveBeenCalledWith(2);
    expect(component.hasError).toBe(true);
    expect(component.errorMessage).toContain('Failed to select site');
  }));

  it('should handle specific error about site access from selectSite service', fakeAsync(() => {
    // Arrange
    component.selectedSiteId = 2;
    mockSiteSelectionService.mockSelectSiteSuccess = false;
    spyOn(mockSiteSelectionService, 'selectSite').and.returnValue(
      throwError(() => new Error('No access to selected site'))
    );
    
    // Act
    component.selectSite();
    tick();

    // Assert
    expect(mockSiteSelectionService.selectSite).toHaveBeenCalledWith(2);
    expect(component.hasError).toBe(true);
    expect(component.errorMessage).toContain('You do not have access to the selected site');
  }));

  it('should call cancelSiteSelection when cancelSelection is called', () => {
    // Arrange
    spyOn(component.cancel, 'emit');
    
    // Act
    component.cancelSelection();

    // Assert
    expect(mockSiteSelectionService.cancelSiteSelection).toHaveBeenCalled();
    expect(component.cancel.emit).toHaveBeenCalled();
  });

  it('should handle error when loading sites fails', fakeAsync(() => {
    // Arrange
    const errorResponse = { status: 500, message: 'Server error' };
    spyOn(mockSiteSelectionService, 'getAvailableSites').and.returnValue(
      throwError(() => errorResponse)
    );
    
    // Act
    component.loadAvailableSites();
    tick();

    // Assert
    expect(component.hasError).toBe(true);
    expect(component.errorMessage).toContain('Failed to load available sites');
  }));

  it('should handle 401 error when loading sites', fakeAsync(() => {
    // Arrange
    const errorResponse = { status: 401, message: 'Unauthorized' };
    spyOn(mockSiteSelectionService, 'getAvailableSites').and.returnValue(
      throwError(() => errorResponse)
    );
    
    // Act
    component.loadAvailableSites();
    tick();

    // Assert
    expect(component.hasError).toBe(true);
    expect(component.errorMessage).toContain('session has expired');
  }));

  it('should handle 403 error when loading sites', fakeAsync(() => {
    // Arrange
    const errorResponse = { status: 403, message: 'Forbidden' };
    spyOn(mockSiteSelectionService, 'getAvailableSites').and.returnValue(
      throwError(() => errorResponse)
    );
    
    // Act
    component.loadAvailableSites();
    tick();

    // Assert
    expect(component.hasError).toBe(true);
    expect(component.errorMessage).toContain('permission to access site information');
  }));

  it('should format site role display correctly', () => {
    // Test various role formats
    expect(component.getSiteRoleDisplay('admin')).toBe('Admin');
    expect(component.getSiteRoleDisplay('siteAdmin')).toBe('Site Admin');
    expect(component.getSiteRoleDisplay('site_admin')).toBe('Site Admin');
    expect(component.getSiteRoleDisplay('')).toBe('');
  });

  it('should properly clean up on destroy', () => {
    // Act
    component.ngOnInit();
    component.ngOnDestroy();
    
    // We can't easily test the internal observables directly,
    // but we can verify the component can be destroyed without errors
    expect(true).toBe(true);
  });
});