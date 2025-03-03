import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Router, ActivatedRoute, convertToParamMap } from '@angular/router';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ReactiveFormsModule, FormBuilder } from '@angular/forms';
import { BehaviorSubject, of, throwError } from 'rxjs';

import { InteractionEditPageComponent } from './interaction-edit-page.component';
import { Interaction, InteractionFormModel } from '../../models/interaction.model';
import { InteractionService } from '../../services/interaction.service';
import { InteractionFormService } from '../../services/interaction-form.service';
import { BreadcrumbService } from '../../../../shared/services/breadcrumb.service';
import { ToastService } from '../../../../shared/services/toast.service';
import { ErrorHandlerService } from '../../../../core/errors/error-handler.service';

// Helper function to create a mock ActivatedRoute with params
function createMockActivatedRoute(params: any) {
  return {
    paramMap: of(convertToParamMap(params)),
    queryParamMap: of(convertToParamMap({})),
    params: of(params)
  };
}

describe('InteractionEditPageComponent', () => {
  let component: InteractionEditPageComponent;
  let fixture: ComponentFixture<InteractionEditPageComponent>;
  let mockRouter: jasmine.SpyObj<Router>;
  let mockActivatedRoute: any;
  let mockInteractionService: jasmine.SpyObj<InteractionService>;
  let mockFormService: jasmine.SpyObj<InteractionFormService>;
  let mockBreadcrumbService: jasmine.SpyObj<BreadcrumbService>;
  let mockToastService: jasmine.SpyObj<ToastService>;
  let mockErrorHandler: jasmine.SpyObj<ErrorHandlerService>;
  let loadingSubject: BehaviorSubject<boolean>;
  let submittingSubject: BehaviorSubject<boolean>;
  let mockInteraction: Interaction;

  beforeEach(() => {
    // Create mock interaction data
    mockInteraction = {
      id: 123,
      siteId: 1,
      title: 'Test Interaction',
      type: 'Meeting',
      lead: 'John Smith',
      startDatetime: new Date(),
      endDatetime: new Date(Date.now() + 3600000), // 1 hour later
      timezone: 'America/New_York',
      location: 'Conference Room A',
      description: 'Test description',
      notes: 'Test notes',
      createdBy: 1,
      createdAt: new Date(),
      updatedAt: new Date()
    };

    // Create mock services
    mockRouter = jasmine.createSpyObj('Router', ['navigate']);
    
    // Set up ActivatedRoute with ID parameter
    mockActivatedRoute = createMockActivatedRoute({ id: '123' });
    
    // Initialize loadingSubject and submittingSubject as BehaviorSubjects
    loadingSubject = new BehaviorSubject<boolean>(false);
    submittingSubject = new BehaviorSubject<boolean>(false);
    
    // Create spy objects for all required services
    mockInteractionService = jasmine.createSpyObj('InteractionService', 
      ['getInteraction', 'updateInteraction']);
    mockInteractionService.getInteraction.and.returnValue(of(mockInteraction));
    
    mockFormService = jasmine.createSpyObj('InteractionFormService', 
      ['getInteraction', 'updateInteraction', 'interactionForm']);
    mockFormService.getInteraction.and.returnValue(of(mockInteraction));
    mockFormService.updateInteraction.and.returnValue(of(mockInteraction));
    
    // Set up loadingSubject and submittingSubject to be returned by FormService observables
    Object.defineProperty(mockFormService, 'loading$', { get: () => loadingSubject.asObservable() });
    Object.defineProperty(mockFormService, 'submitting$', { get: () => submittingSubject.asObservable() });
    
    mockBreadcrumbService = jasmine.createSpyObj('BreadcrumbService', ['setBreadcrumbs']);
    mockToastService = jasmine.createSpyObj('ToastService', ['showSuccess', 'showError']);
    mockErrorHandler = jasmine.createSpyObj('ErrorHandlerService', ['handleError']);

    TestBed.configureTestingModule({
      declarations: [InteractionEditPageComponent],
      imports: [
        HttpClientTestingModule,
        ReactiveFormsModule
      ],
      providers: [
        FormBuilder,
        { provide: Router, useValue: mockRouter },
        { provide: ActivatedRoute, useValue: mockActivatedRoute },
        { provide: InteractionService, useValue: mockInteractionService },
        { provide: InteractionFormService, useValue: mockFormService },
        { provide: BreadcrumbService, useValue: mockBreadcrumbService },
        { provide: ToastService, useValue: mockToastService },
        { provide: ErrorHandlerService, useValue: mockErrorHandler }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(InteractionEditPageComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should load interaction on init', () => {
    // Call component.ngOnInit()
    component.ngOnInit();
    
    // Expect mockFormService.getInteraction to have been called with correct ID
    expect(mockFormService.getInteraction).toHaveBeenCalledWith(123);
    
    // Expect component.interaction to equal mock interaction
    expect(component.interaction).toEqual(mockInteraction);
    
    // Expect component.pageTitle to include the mock interaction title
    expect(component.pageTitle).toContain(mockInteraction.title);
    
    // Expect mockBreadcrumbService.setBreadcrumbs to have been called
    expect(mockBreadcrumbService.setBreadcrumbs).toHaveBeenCalled();
  });

  it('should handle loading state', () => {
    // Call component.ngOnInit()
    component.ngOnInit();
    
    // Set loadingSubject.next(true)
    loadingSubject.next(true);
    
    // Expect component.loading to be true
    expect(component.loading).toBeTrue();
    
    // Set loadingSubject.next(false)
    loadingSubject.next(false);
    
    // Expect component.loading to be false
    expect(component.loading).toBeFalse();
  });

  it('should handle submission state', () => {
    // Call component.ngOnInit()
    component.ngOnInit();
    
    // Set submittingSubject.next(true)
    submittingSubject.next(true);
    
    // Expect component.submitting to be true
    expect(component.submitting).toBeTrue();
    
    // Set submittingSubject.next(false)
    submittingSubject.next(false);
    
    // Expect component.submitting to be false
    expect(component.submitting).toBeFalse();
  });

  it('should submit form and show success', () => {
    // Call component.ngOnInit()
    component.ngOnInit();
    
    // Call component.onSubmit()
    component.onSubmit();
    
    // Expect mockFormService.updateInteraction to have been called with correct ID
    expect(mockFormService.updateInteraction).toHaveBeenCalledWith(123);
    
    // Expect mockToastService.showSuccess to have been called
    expect(mockToastService.showSuccess).toHaveBeenCalled();
    
    // Expect mockRouter.navigate to have been called
    expect(mockRouter.navigate).toHaveBeenCalled();
  });

  it('should handle submission error', () => {
    // Reconfigure mockFormService.updateInteraction to return an error
    const testError = new Error('Test error');
    mockFormService.updateInteraction.and.returnValue(throwError(() => testError));
    
    // Call component.ngOnInit()
    component.ngOnInit();
    
    // Call component.onSubmit()
    component.onSubmit();
    
    // Expect mockErrorHandler.handleError to have been called with the error
    expect(mockErrorHandler.handleError).toHaveBeenCalledWith(testError);
    
    // Expect mockToastService.showError to have been called
    expect(mockToastService.showError).toHaveBeenCalled();
  });

  it('should handle cancel action', () => {
    // Call component.onCancel()
    component.onCancel();
    
    // Expect mockRouter.navigate to have been called with correct path
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/interactions']);
  });

  it('should clean up subscriptions on destroy', () => {
    // Create spy on component.destroy$.next
    spyOn(component.destroy$, 'next');
    
    // Create spy on component.destroy$.complete
    spyOn(component.destroy$, 'complete');
    
    // Call component.ngOnDestroy()
    component.ngOnDestroy();
    
    // Expect component.destroy$.next to have been called with no arguments
    expect(component.destroy$.next).toHaveBeenCalled();
    
    // Expect component.destroy$.complete to have been called
    expect(component.destroy$.complete).toHaveBeenCalled();
  });
});