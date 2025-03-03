import { ComponentFixture, TestBed, waitForAsync, fakeAsync, tick } from '@angular/core/testing'; // v16.2.0
import { Router } from '@angular/router'; // v16.2.0
import { RouterTestingModule } from '@angular/router/testing'; // v16.2.0
import { Title } from '@angular/platform-browser'; // v16.2.0
import { ReactiveFormsModule } from '@angular/forms'; // v16.2.0
import { BehaviorSubject, of, throwError } from 'rxjs'; // v7.8.1

import { InteractionCreatePageComponent } from './interaction-create-page.component';
import { InteractionFormComponent } from '../../components/interaction-form/interaction-form.component';
import { Interaction } from '../../models/interaction.model';
import { InteractionService } from '../../services/interaction.service';
import { InteractionFormService } from '../../services/interaction-form.service';
import { SiteSelectionService } from '../../../../core/auth/site-selection.service';
import { ToastService } from '../../../../shared/services/toast.service';
import { BreadcrumbService } from '../../../../shared/services/breadcrumb.service';

// Mock objects
const mockRouter = {
  navigate: jasmine.createSpy('navigate')
};

const mockTitleService = {
  setTitle: jasmine.createSpy('setTitle')
};

const mockInteractionService = {
  createInteraction: jasmine.createSpy('createInteraction').and.returnValue(of({})),
  loading$: new BehaviorSubject<boolean>(false)
};

const mockFormService = {
  initializeForm: jasmine.createSpy('initializeForm'),
  validateAndGetFormData: jasmine.createSpy('validateAndGetFormData'),
  interactionForm: {
    valueChanges: new BehaviorSubject({}).asObservable()
  }
};

const mockSiteService = {
  getCurrentSiteId: jasmine.createSpy('getCurrentSiteId').and.returnValue(1)
};

const mockToastService = {
  showSuccess: jasmine.createSpy('showSuccess'),
  showError: jasmine.createSpy('showError')
};

const mockBreadcrumbService = {
  setBreadcrumbs: jasmine.createSpy('setBreadcrumbs')
};

const mockInteraction = {
  title: 'Test Interaction',
  type: 'Meeting',
  lead: 'John Smith',
  startDatetime: new Date(),
  endDatetime: new Date(),
  timezone: 'America/New_York',
  description: 'Test description',
  location: 'Test location'
};

describe('InteractionCreatePageComponent', () => {
  let component: InteractionCreatePageComponent;
  let fixture: ComponentFixture<InteractionCreatePageComponent>;
  let interactionService: any;
  let formService: any;
  let siteService: any;
  let toastService: any;
  let breadcrumbService: any;
  let router: any;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      imports: [
        RouterTestingModule,
        ReactiveFormsModule
      ],
      declarations: [
        InteractionCreatePageComponent
      ],
      providers: [
        { provide: Router, useValue: mockRouter },
        { provide: InteractionService, useValue: mockInteractionService },
        { provide: InteractionFormService, useValue: mockFormService },
        { provide: SiteSelectionService, useValue: mockSiteService },
        { provide: ToastService, useValue: mockToastService },
        { provide: BreadcrumbService, useValue: mockBreadcrumbService }
      ]
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(InteractionCreatePageComponent);
    component = fixture.componentInstance;
    interactionService = TestBed.inject(InteractionService);
    formService = TestBed.inject(InteractionFormService);
    siteService = TestBed.inject(SiteSelectionService);
    toastService = TestBed.inject(ToastService);
    breadcrumbService = TestBed.inject(BreadcrumbService);
    router = TestBed.inject(Router);
    
    // Reset spies for each test
    mockRouter.navigate.calls.reset();
    mockInteractionService.createInteraction.calls.reset();
    mockFormService.initializeForm.calls.reset();
    mockFormService.validateAndGetFormData.calls.reset();
    mockSiteService.getCurrentSiteId.calls.reset();
    mockToastService.showSuccess.calls.reset();
    mockToastService.showError.calls.reset();
    mockBreadcrumbService.setBreadcrumbs.calls.reset();
    
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize the form on init', () => {
    component.ngOnInit();
    expect(mockFormService.initializeForm).toHaveBeenCalled();
  });

  it('should set up breadcrumbs on init', () => {
    component.ngOnInit();
    expect(mockBreadcrumbService.setBreadcrumbs).toHaveBeenCalledWith([
      { label: 'Dashboard', url: '/dashboard' },
      { label: 'Interactions', url: '/interactions' },
      { label: 'Create New', url: '/interactions/create' }
    ]);
  });

  it('should subscribe to form value changes to reset errors', () => {
    // Setup
    component.hasFormErrors = true;
    
    // Create a new BehaviorSubject for the test
    const valueChangesSubject = new BehaviorSubject({});
    
    // Override the interactionForm's valueChanges with our test subject
    formService.interactionForm = {
      valueChanges: valueChangesSubject
    };
    
    // Initialize component to set up subscriptions
    component.ngOnInit();
    
    // Trigger form value changes
    valueChangesSubject.next({});
    
    // Verify error flag was reset
    expect(component.hasFormErrors).toBe(false);
  });

  it('should handle form submission with valid data', fakeAsync(() => {
    // Setup form validation to return valid data
    mockFormService.validateAndGetFormData.and.returnValue(mockInteraction);
    mockInteractionService.createInteraction.and.returnValue(of({ id: 1, ...mockInteraction }));
    
    // Call onSave
    component.onSave();
    tick();
    
    // Verify interactions with dependencies
    expect(mockFormService.validateAndGetFormData).toHaveBeenCalled();
    expect(mockSiteService.getCurrentSiteId).toHaveBeenCalled();
    expect(mockInteractionService.createInteraction).toHaveBeenCalledWith(
      jasmine.objectContaining({ ...mockInteraction, siteId: 1 })
    );
    expect(mockToastService.showSuccess).toHaveBeenCalledWith('Interaction created successfully');
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/interactions']);
  }));

  it('should not submit when form is invalid', () => {
    // Setup form validation to return null (invalid form)
    mockFormService.validateAndGetFormData.and.returnValue(null);
    
    // Call onSave
    component.onSave();
    
    // Verify interactions with dependencies
    expect(mockFormService.validateAndGetFormData).toHaveBeenCalled();
    expect(mockInteractionService.createInteraction).not.toHaveBeenCalled();
    expect(mockToastService.showSuccess).not.toHaveBeenCalled();
    expect(mockRouter.navigate).not.toHaveBeenCalled();
    expect(component.hasFormErrors).toBe(true);
  });

  it('should handle API errors during submission', fakeAsync(() => {
    // Setup form validation to return valid data
    mockFormService.validateAndGetFormData.and.returnValue(mockInteraction);
    
    // Setup API to return an error
    const errorMessage = 'API Error';
    mockInteractionService.createInteraction.and.returnValue(
      throwError(() => new Error(errorMessage))
    );
    
    // Call onSave
    component.onSave();
    tick();
    
    // Verify error handling
    expect(mockToastService.showError).toHaveBeenCalledWith(
      `Failed to create interaction: ${errorMessage}`
    );
    expect(mockRouter.navigate).not.toHaveBeenCalled();
  }));

  it('should add site ID to interaction data when submitting', fakeAsync(() => {
    // Set up form validation to return valid data without siteId
    const interactionWithoutSite = { ...mockInteraction };
    delete interactionWithoutSite.siteId;
    
    mockFormService.validateAndGetFormData.and.returnValue(interactionWithoutSite);
    mockInteractionService.createInteraction.and.returnValue(of({ id: 1, ...interactionWithoutSite, siteId: 1 }));
    
    // Call onSave
    component.onSave();
    tick();
    
    // Verify siteId was added
    expect(mockInteractionService.createInteraction).toHaveBeenCalledWith(
      jasmine.objectContaining({ siteId: 1 })
    );
  }));

  it('should track loading state from interaction service', () => {
    // Simulate loading state change
    mockInteractionService.loading$.next(true);
    
    // Verify loading state was updated
    expect(component.isLoading).toBe(true);
    
    // Simulate loading completed
    mockInteractionService.loading$.next(false);
    
    // Verify loading state was updated
    expect(component.isLoading).toBe(false);
  });

  it('should navigate back to interactions on cancel', () => {
    component.onCancel();
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/interactions']);
  });

  it('should navigate back to interactions on goBack', () => {
    component.goBack();
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/interactions']);
  });

  it('should unsubscribe when destroyed', () => {
    // Create a spy on the unsubscribe method
    const unsubscribeSpy = jasmine.createSpy('unsubscribe');
    
    // Replace component's subscriptions with a mock that has our spy
    (component as any).subscriptions = { unsubscribe: unsubscribeSpy };
    
    // Call ngOnDestroy
    component.ngOnDestroy();
    
    // Verify unsubscribe was called
    expect(unsubscribeSpy).toHaveBeenCalled();
  });
});