import { ComponentFixture, TestBed } from '@angular/core/testing'; // v16.2.0
import { By } from '@angular/platform-browser'; // v16.2.0
import { Router } from '@angular/router'; // v16.2.0
import { of, BehaviorSubject } from 'rxjs'; // v7.8.1

import { BreadcrumbComponent } from './breadcrumb.component';
import { BreadcrumbService } from '../../services/breadcrumb.service';

describe('BreadcrumbComponent', () => {
  let component: BreadcrumbComponent;
  let fixture: ComponentFixture<BreadcrumbComponent>;
  let breadcrumbService: jasmine.SpyObj<BreadcrumbService>;
  let router: jasmine.SpyObj<Router>;
  let breadcrumbsSubject: BehaviorSubject<any[]>;

  beforeEach(() => {
    // Create mock breadcrumb data
    breadcrumbsSubject = new BehaviorSubject<any[]>([
      { label: 'Dashboard', url: '/' },
      { label: 'Interactions', url: '/interactions' }
    ]);

    // Create mock services
    breadcrumbService = jasmine.createSpyObj('BreadcrumbService', ['updateBreadcrumbs']);
    Object.defineProperty(breadcrumbService, 'breadcrumbs$', { value: breadcrumbsSubject.asObservable() });

    router = jasmine.createSpyObj('Router', ['navigateByUrl']);

    // Mock UserContextService
    const userContextService = jasmine.createSpyObj('UserContextService', [], {
      currentSite$: of({ id: 1, name: 'Test Site', role: 'admin' })
    });

    TestBed.configureTestingModule({
      declarations: [BreadcrumbComponent],
      providers: [
        { provide: BreadcrumbService, useValue: breadcrumbService },
        { provide: Router, useValue: router },
        { provide: 'UserContextService', useValue: userContextService }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(BreadcrumbComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create the component', () => {
    expect(component).toBeTruthy();
  });

  it('should subscribe to breadcrumbs$ from breadcrumb service on initialization', () => {
    // Spy on the component's breadcrumbService.breadcrumbs$ to verify subscription
    const spy = spyOn(breadcrumbsSubject, 'subscribe').and.callThrough();
    
    // Re-initialize component to trigger subscriptions
    component.ngOnInit();
    
    // Verify the subscription was created
    expect(spy).toHaveBeenCalled();
  });

  it('should render breadcrumbs correctly', () => {
    // Update breadcrumb data
    breadcrumbsSubject.next([
      { label: 'Dashboard', url: '/' },
      { label: 'Interactions', url: '/interactions' },
      { label: 'View', url: '/interactions/123' }
    ]);
    
    fixture.detectChanges();
    
    // Find all breadcrumb items
    const breadcrumbItems = fixture.debugElement.queryAll(By.css('.breadcrumb-item'));
    
    // Verify number of items
    expect(breadcrumbItems.length).toBe(3);
    
    // Verify text and links
    expect(breadcrumbItems[0].nativeElement.textContent).toContain('Dashboard');
    expect(breadcrumbItems[1].nativeElement.textContent).toContain('Interactions');
    expect(breadcrumbItems[2].nativeElement.textContent).toContain('View');
    
    // Check URLs
    const links = fixture.debugElement.queryAll(By.css('.breadcrumb-item a'));
    expect(links[0].attributes['href']).toBe('/');
    expect(links[1].attributes['href']).toBe('/interactions');
  });

  it('should render home link when showHome is true', () => {
    component.showHome = true;
    
    // Update breadcrumb data without home
    breadcrumbsSubject.next([
      { label: 'Interactions', url: '/interactions' }
    ]);
    
    fixture.detectChanges();
    
    // Find home breadcrumb item
    const homeItem = fixture.debugElement.query(By.css('.breadcrumb-item:first-child'));
    
    // Home link should exist and contain Dashboard text
    expect(homeItem).toBeTruthy();
    expect(homeItem.nativeElement.textContent).toContain('Dashboard');
  });

  it('should not render home link when showHome is false', () => {
    component.showHome = false;
    
    // Update breadcrumb data without home
    breadcrumbsSubject.next([
      { label: 'Interactions', url: '/interactions' }
    ]);
    
    fixture.detectChanges();
    
    // First breadcrumb should not be home
    const firstItem = fixture.debugElement.query(By.css('.breadcrumb-item:first-child'));
    expect(firstItem.nativeElement.textContent).toContain('Interactions');
    expect(firstItem.nativeElement.textContent).not.toContain('Dashboard');
  });

  it('should call router.navigate when navigateTo is called', () => {
    const url = '/interactions';
    const mockEvent = jasmine.createSpyObj('MouseEvent', ['preventDefault']);
    
    component.navigateTo(url, mockEvent);
    
    expect(mockEvent.preventDefault).toHaveBeenCalled();
    expect(router.navigateByUrl).toHaveBeenCalledWith(url);
  });

  it('should apply active class to the last breadcrumb', () => {
    // Update breadcrumb data
    breadcrumbsSubject.next([
      { label: 'Dashboard', url: '/' },
      { label: 'Interactions', url: '/interactions' },
      { label: 'View', url: '/interactions/123' }
    ]);
    
    fixture.detectChanges();
    
    // Get all breadcrumb items
    const breadcrumbItems = fixture.debugElement.queryAll(By.css('.breadcrumb-item'));
    
    // First and second items should not have active class
    expect(breadcrumbItems[0].nativeElement.classList.contains('active')).toBeFalsy();
    expect(breadcrumbItems[1].nativeElement.classList.contains('active')).toBeFalsy();
    
    // Last item should have active class
    expect(breadcrumbItems[2].nativeElement.classList.contains('active')).toBeTruthy();
  });

  it('should unsubscribe on component destruction', () => {
    // Create spy on the destroy$ subject's next method
    const nextSpy = spyOn<any>(component['destroy$'], 'next');
    const completeSpy = spyOn<any>(component['destroy$'], 'complete');
    
    // Call ngOnDestroy
    component.ngOnDestroy();
    
    // Verify the subject was completed
    expect(nextSpy).toHaveBeenCalled();
    expect(completeSpy).toHaveBeenCalled();
  });

  it('should handle empty breadcrumbs array', () => {
    // Update breadcrumb data to empty array
    breadcrumbsSubject.next([]);
    
    fixture.detectChanges();
    
    // There should be no breadcrumb items
    const breadcrumbItems = fixture.debugElement.queryAll(By.css('.breadcrumb-item'));
    expect(breadcrumbItems.length).toBe(0);
    
    // The nav element should still exist but be empty
    const nav = fixture.debugElement.query(By.css('nav'));
    expect(nav).toBeTruthy();
  });
});