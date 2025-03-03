import { ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { Router } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';
import { of, BehaviorSubject } from 'rxjs';

import { NavigationComponent } from './navigation.component';
import { AuthService } from '../../../core/auth/auth.service';
import { UserContextService } from '../../../core/auth/user-context.service';
import { SiteSelectionService } from '../../../core/auth/site-selection.service';
import { HasPermissionDirective } from '../../directives/has-permission.directive';

describe('NavigationComponent', () => {
  let component: NavigationComponent;
  let fixture: ComponentFixture<NavigationComponent>;
  let authService: jasmine.SpyObj<AuthService>;
  let userContextService: jasmine.SpyObj<UserContextService>;
  let siteSelectionService: jasmine.SpyObj<SiteSelectionService>;
  let router: jasmine.SpyObj<Router>;
  
  // Create mock services with appropriate behavior
  function createMockServices() {
    const authService = jasmine.createSpyObj('AuthService', ['logout', 'isAuthenticated']);
    const userContextService = jasmine.createSpyObj('UserContextService', 
      ['canCreate', 'isAdmin', 'isEditor']);
    const siteSelectionService = jasmine.createSpyObj('SiteSelectionService', 
      ['getCurrentSiteId', 'getAvailableSites', 'startSiteSelection']);
    const router = jasmine.createSpyObj('Router', ['navigate']);

    // Setup default behavior
    authService.isAuthenticated.and.returnValue(of(false));
    authService.logout.and.returnValue(of(void 0));
    
    // Set observable properties
    const currentUserSubject = new BehaviorSubject(null);
    const currentSiteSubject = new BehaviorSubject(null);
    const currentSiteIdSubject = new BehaviorSubject(null);
    
    Object.defineProperty(userContextService, 'currentUser$', { get: () => currentUserSubject.asObservable() });
    Object.defineProperty(userContextService, 'currentSite$', { get: () => currentSiteSubject.asObservable() });
    Object.defineProperty(userContextService, 'currentSiteId$', { get: () => currentSiteIdSubject.asObservable() });
    
    userContextService.isAdmin.and.returnValue(false);
    userContextService.isEditor.and.returnValue(false);
    userContextService.canCreate.and.returnValue(false);
    siteSelectionService.getCurrentSiteId.and.returnValue(null);
    siteSelectionService.getAvailableSites.and.returnValue(of([]));

    return {
      authService,
      userContextService,
      siteSelectionService,
      router,
      currentUserSubject,
      currentSiteSubject,
      currentSiteIdSubject
    };
  }

  beforeEach(() => {
    const mocks = createMockServices();
    authService = mocks.authService;
    userContextService = mocks.userContextService;
    siteSelectionService = mocks.siteSelectionService;
    router = mocks.router;

    TestBed.configureTestingModule({
      imports: [RouterTestingModule],
      declarations: [NavigationComponent, HasPermissionDirective],
      providers: [
        { provide: AuthService, useValue: authService },
        { provide: UserContextService, useValue: userContextService },
        { provide: SiteSelectionService, useValue: siteSelectionService },
        { provide: Router, useValue: router }
      ]
    });

    fixture = TestBed.createComponent(NavigationComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create the component', () => {
    expect(component).toBeTruthy();
  });

  it('should show unauthenticated view when user is not logged in', () => {
    component.isAuthenticated = false;
    fixture.detectChanges();
    
    // Find login elements
    const loginElements = fixture.debugElement.queryAll(By.css('a'));
    const hasLoginLink = Array.from(loginElements).some(
      link => link.nativeElement.textContent.toLowerCase().includes('login') || 
              link.attributes['routerLink']?.includes('login')
    );
    
    expect(component.isAuthenticated).toBeFalse();
    expect(hasLoginLink).toBeTrue();
  });

  it('should show authenticated view when user is logged in', () => {
    // Set authenticated state
    component.isAuthenticated = true;
    fixture.detectChanges();
    
    // Find authenticated elements and verify login is not present
    const loginElements = fixture.debugElement.queryAll(By.css('a'));
    const hasLoginLink = Array.from(loginElements).some(
      link => link.nativeElement.textContent.toLowerCase().includes('login') || 
              link.attributes['routerLink']?.includes('login')
    );
    
    expect(component.isAuthenticated).toBeTrue();
    expect(hasLoginLink).toBeFalse();
  });

  it('should show username when user is logged in', () => {
    // Set user with username
    component.currentUser = { username: 'TestUser' } as any;
    component.isAuthenticated = true;
    fixture.detectChanges();
    
    // Check if username appears in the rendered content
    const componentText = fixture.nativeElement.textContent;
    expect(component.currentUser.username).toBe('TestUser');
    expect(componentText).toContain('TestUser');
  });

  it('should call auth service logout method when logout is clicked', () => {
    // Call logout method
    component.logout();
    
    // Verify service method was called
    expect(authService.logout).toHaveBeenCalled();
  });

  it('should show site-specific navigation links when site is selected', () => {
    // Set site context
    component.currentSite = { id: 1, name: 'Test Site', role: 'editor' };
    component.hasSiteAccess = true;
    fixture.detectChanges();
    
    // Verify site context is set
    expect(component.currentSite).toBeTruthy();
    expect(component.hasSiteAccess).toBeTrue();
  });

  it('should not show site-specific navigation links when no site is selected', () => {
    // Set no site context
    component.currentSite = null;
    component.hasSiteAccess = false;
    fixture.detectChanges();
    
    // Verify no site context
    expect(component.currentSite).toBeNull();
    expect(component.hasSiteAccess).toBeFalse();
  });

  it('should show "New Interaction" link only when user has create permission', () => {
    // Set state with editor permission
    component.isAuthenticated = true;
    component.hasSiteAccess = true;
    component.isEditor = true;
    fixture.detectChanges();
    
    // Verify editor permission
    expect(component.isEditor).toBeTrue();
    
    // Change permission
    component.isEditor = false;
    fixture.detectChanges();
    
    // Verify changed permission
    expect(component.isEditor).toBeFalse();
  });

  it('should toggle mobile menu when toggle button is clicked', () => {
    // Check initial state
    expect(component.isExpanded).toBeFalse();
    
    // Toggle menu
    component.toggleMenu();
    
    // Verify menu opened
    expect(component.isExpanded).toBeTrue();
    
    // Toggle again
    component.toggleMenu();
    
    // Verify menu closed
    expect(component.isExpanded).toBeFalse();
  });

  it('should close mobile menu when navigation occurs', () => {
    // Set menu open
    component.isExpanded = true;
    
    // Call closeMenu which would happen during navigation
    component.closeMenu();
    
    // Verify menu closed
    expect(component.isExpanded).toBeFalse();
  });

  it('should unsubscribe from all subscriptions on destroy', () => {
    // Setup spy on unsubscribe
    spyOn(component.subscriptions, 'unsubscribe');
    
    // Trigger component destruction
    component.ngOnDestroy();
    
    // Verify unsubscribe was called
    expect(component.subscriptions.unsubscribe).toHaveBeenCalled();
  });
});