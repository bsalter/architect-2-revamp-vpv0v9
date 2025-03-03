import { ComponentFixture, TestBed } from '@angular/core/testing'; // v16.2.0
import { FormGroup, ReactiveFormsModule, FormBuilder } from '@angular/forms'; // v16.2.0
import { Router, ActivatedRoute, RouterModule } from '@angular/router'; // v16.2.0
import { RouterTestingModule } from '@angular/router/testing'; // v16.2.0
import { BehaviorSubject, of } from 'rxjs'; // v7.8.1

import { InteractionFormComponent } from './interaction-form.component';
import { InteractionFormService } from '../../services/interaction-form.service';
import { InteractionService } from '../../services/interaction.service';
import { SiteSelectionService } from '../../../core/auth/site-selection.service';
import { Interaction, InteractionType } from '../../models/interaction.model';
import { ToastService } from '../../../shared/services/toast.service';

describe('InteractionFormComponent', () => {
  let component: InteractionFormComponent;
  let fixture: ComponentFixture<InteractionFormComponent>;
  let mockInteractionFormService: jasmine.SpyObj<InteractionFormService>;
  let mockInteractionService: jasmine.SpyObj<InteractionService>;
  let mockToastService: jasmine.SpyObj<ToastService>;
  let mockRouter: jasmine.SpyObj<Router>;
  let mockRoute: any;
  let mockFormBuilder: FormBuilder;
  let mockSiteSelectionService: jasmine.SpyObj<SiteSelectionService>;

  const mockInteraction: Interaction = {
    id: 1,
    siteId: 10,
    title: 'Test Meeting',
    type: InteractionType.MEETING,
    lead: 'John Doe',
    startDatetime: new Date('2023-06-15T10:00:00Z'),
    endDatetime: new Date('2023-06-15T11:00:00Z'),
    timezone: 'America/New_York',
    location: 'Conference Room A',
    description: 'Project planning meeting',
    notes: 'Bring project documents',
    createdBy: 1,
    createdAt: new Date(),
    updatedAt: new Date()
  };

  const mockInteractionTypes = [
    { value: InteractionType.MEETING, label: 'Meeting' },
    { value: InteractionType.CALL, label: 'Call' },
    { value: InteractionType.EMAIL, label: 'Email' },
    { value: InteractionType.OTHER, label: 'Other' }
  ];

  const mockTimezones = [
    'America/New_York',
    'America/Chicago',
    'America/Denver',
    'America/Los_Angeles',
    'Europe/London'
  ];

  // Helper function to create component with specific testing configuration
  async function createComponent(isEditMode = false, testInteraction: any = null): Promise<ComponentFixture<InteractionFormComponent>> {
    // Create spy objects for all dependencies
    mockInteractionFormService = jasmine.createSpyObj('InteractionFormService', [
      'interactionForm',
      'loading$',
      'getInteractionTypes',
      'getTimezones',
      'initializeForm',
      'patchFormWithInteraction',
      'submitForm',
      'isFieldInvalid',
      'getFormErrors'
    ]);
    
    mockInteractionService = jasmine.createSpyObj('InteractionService', [
      'getInteraction',
      'createInteraction',
      'updateInteraction'
    ]);
    
    mockToastService = jasmine.createSpyObj('ToastService', [
      'showSuccess',
      'showError'
    ]);
    
    mockRouter = jasmine.createSpyObj('Router', ['navigate']);
    
    mockSiteSelectionService = jasmine.createSpyObj('SiteSelectionService', ['getCurrentSiteId']);
    mockSiteSelectionService.getCurrentSiteId.and.returnValue(10);

    // Create a mock form group using the actual FormBuilder
    mockFormBuilder = new FormBuilder();
    const testForm = mockFormBuilder.group({
      title: [''],
      type: [''],
      lead: [''],
      startDatetime: [''],
      endDatetime: [''],
      timezone: [''],
      location: [''],
      description: [''],
      notes: ['']
    });

    // Set up mock behavior for form service
    mockInteractionFormService.interactionForm = testForm;
    mockInteractionFormService.loading$ = new BehaviorSubject<boolean>(false);
    mockInteractionFormService.getInteractionTypes.and.returnValue(mockInteractionTypes);
    mockInteractionFormService.getTimezones.and.returnValue(mockTimezones);
    mockInteractionFormService.initializeForm.and.returnValue(testForm);
    mockInteractionFormService.patchFormWithInteraction.and.callFake((interaction) => {
      testForm.patchValue(interaction);
      return testForm;
    });
    mockInteractionFormService.submitForm.and.returnValue(of(testInteraction || mockInteraction));
    mockInteractionFormService.isFieldInvalid.and.returnValue(false);
    mockInteractionFormService.getFormErrors.and.returnValue('');

    // Setup mock route with params observable
    mockRoute = {
      params: of({})
    };

    // Configure mock interaction service
    mockInteractionService.getInteraction.and.returnValue(of(mockInteraction));

    // Configure TestBed with necessary imports and providers
    await TestBed.configureTestingModule({
      imports: [
        ReactiveFormsModule,
        RouterTestingModule
      ],
      declarations: [InteractionFormComponent],
      providers: [
        { provide: InteractionFormService, useValue: mockInteractionFormService },
        { provide: InteractionService, useValue: mockInteractionService },
        { provide: ToastService, useValue: mockToastService },
        { provide: Router, useValue: mockRouter },
        { provide: ActivatedRoute, useValue: mockRoute },
        { provide: SiteSelectionService, useValue: mockSiteSelectionService }
      ]
    }).compileComponents();

    // Create component fixture
    const fixture = TestBed.createComponent(InteractionFormComponent);
    const component = fixture.componentInstance;
    
    // Set up component inputs based on parameters
    component.isEditMode = isEditMode;
    if (testInteraction) {
      component.interaction = testInteraction;
    }
    
    // Trigger change detection
    fixture.detectChanges();
    return fixture;
  }

  it('should create component', async () => {
    fixture = await createComponent();
    component = fixture.componentInstance;
    expect(component).toBeTruthy();
  });

  it('should initialize form in create mode', async () => {
    fixture = await createComponent(false);
    component = fixture.componentInstance;
    
    expect(component.isEditMode).toBeFalse();
    expect(component.formTitle).toBe('Create New Interaction');
    expect(mockInteractionFormService.initializeForm).toHaveBeenCalled();
  });

  it('should initialize form in edit mode', async () => {
    fixture = await createComponent(true, mockInteraction);
    component = fixture.componentInstance;
    
    expect(component.isEditMode).toBeTrue();
    expect(component.formTitle).toBe('Edit Interaction');
    expect(mockInteractionFormService.patchFormWithInteraction).toHaveBeenCalledWith(mockInteraction);
  });

  it('should load interaction types and timezones', async () => {
    fixture = await createComponent();
    component = fixture.componentInstance;
    
    expect(component.interactionTypes).toEqual(mockInteractionTypes);
    expect(component.timezones).toEqual(mockTimezones);
    expect(mockInteractionFormService.getInteractionTypes).toHaveBeenCalled();
    expect(mockInteractionFormService.getTimezones).toHaveBeenCalled();
  });

  it('should mark form as invalid with empty required fields', async () => {
    fixture = await createComponent();
    component = fixture.componentInstance;
    
    // Set up the validation error behavior
    mockInteractionFormService.isFieldInvalid.and.returnValue(true);
    mockInteractionFormService.getFormErrors.and.returnValue('This field is required');
    
    // Make the form invalid
    component.form.get('title').setValue('');
    component.form.get('title').markAsTouched();
    fixture.detectChanges();
    
    // Check if validation is working
    expect(component.isFieldInvalid('title')).toBeTrue();
    expect(component.getErrorMessage('title')).toBe('This field is required');
    expect(component.form.valid).toBeFalse();
  });

  it('should validate title minimum length', async () => {
    fixture = await createComponent();
    component = fixture.componentInstance;
    
    // Set up the validation error behavior
    mockInteractionFormService.isFieldInvalid.and.callFake((controlName) => {
      return controlName === 'title';
    });
    mockInteractionFormService.getFormErrors.and.returnValue('This field is too short');
    
    // Make title too short
    component.form.get('title').setValue('Test');
    component.form.get('title').markAsTouched();
    fixture.detectChanges();
    
    // Check if validation is working
    expect(component.isFieldInvalid('title')).toBeTrue();
    expect(component.getErrorMessage('title')).toBe('This field is too short');
  });

  it('should validate endDatetime after startDatetime', async () => {
    fixture = await createComponent();
    component = fixture.componentInstance;
    
    // Set up the validation error behavior
    mockInteractionFormService.isFieldInvalid.and.callFake((controlName) => {
      return controlName === 'endDatetime';
    });
    mockInteractionFormService.getFormErrors.and.returnValue('End date must be after start date');
    
    // Set invalid dates (end before start)
    component.form.get('startDatetime').setValue(new Date('2023-06-15T11:00:00Z'));
    component.form.get('endDatetime').setValue(new Date('2023-06-15T10:00:00Z'));
    component.form.get('endDatetime').markAsTouched();
    fixture.detectChanges();
    
    // Check if validation is working
    expect(component.isFieldInvalid('endDatetime')).toBeTrue();
    expect(component.getErrorMessage('endDatetime')).toBe('End date must be after start date');
  });

  it('should emit formSubmitted event on valid form submission in create mode', async () => {
    fixture = await createComponent(false);
    component = fixture.componentInstance;
    
    // Create a spy on the formSubmitted event emitter
    spyOn(component.formSubmitted, 'emit');
    
    // Make sure form is valid
    component.form.patchValue(mockInteraction);
    
    // Call the submit method
    component.onSubmit();
    
    // Check that form was submitted and event emitted
    expect(mockInteractionFormService.submitForm).toHaveBeenCalled();
    expect(component.formSubmitted.emit).toHaveBeenCalledWith(mockInteraction);
    expect(mockToastService.showSuccess).toHaveBeenCalled();
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/interactions']);
  });

  it('should emit formSubmitted event on valid form submission in edit mode', async () => {
    fixture = await createComponent(true, mockInteraction);
    component = fixture.componentInstance;
    
    // Create a spy on the formSubmitted event emitter
    spyOn(component.formSubmitted, 'emit');
    
    // Update form values
    const updatedInteraction = {
      ...mockInteraction,
      title: 'Updated Meeting Title'
    };
    mockInteractionFormService.submitForm.and.returnValue(of(updatedInteraction));
    
    // Call the submit method
    component.onSubmit();
    
    // Check that form was submitted and event emitted with updated data
    expect(mockInteractionFormService.submitForm).toHaveBeenCalled();
    expect(component.formSubmitted.emit).toHaveBeenCalledWith(updatedInteraction);
    expect(mockToastService.showSuccess).toHaveBeenCalled();
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/interactions']);
  });

  it('should not submit form when invalid', async () => {
    fixture = await createComponent();
    component = fixture.componentInstance;
    
    // Create a spy on the formSubmitted event emitter
    spyOn(component.formSubmitted, 'emit');
    
    // Make the form invalid
    component.form.get('title').setValue('');
    mockInteractionFormService.submitForm.and.returnValue(of(null));
    
    // Call the submit method
    component.onSubmit();
    
    // Verify the form submission was attempted but no event emitted
    expect(mockInteractionFormService.submitForm).toHaveBeenCalled();
    expect(component.formSubmitted.emit).not.toHaveBeenCalled();
  });

  it('should emit formCancelled event when cancel is clicked', async () => {
    fixture = await createComponent();
    component = fixture.componentInstance;
    
    // Create a spy on the formCancelled event emitter
    spyOn(component.formCancelled, 'emit');
    
    // Call the cancel method
    component.onCancel();
    
    // Check that event was emitted and navigation occurred
    expect(component.formCancelled.emit).toHaveBeenCalled();
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/interactions']);
  });

  it('should correctly check for field errors', async () => {
    fixture = await createComponent();
    component = fixture.componentInstance;
    
    // Configure the mock to return different errors based on field name
    mockInteractionFormService.isFieldInvalid.and.callFake((controlName) => {
      return controlName === 'title' || controlName === 'description';
    });
    
    mockInteractionFormService.getFormErrors.and.callFake((controlName) => {
      if (controlName === 'title') return 'Title is required';
      if (controlName === 'description') return 'Description is too short';
      return '';
    });
    
    // Check specific error messages for different fields
    expect(component.isFieldInvalid('title')).toBeTrue();
    expect(component.getErrorMessage('title')).toBe('Title is required');
    
    expect(component.isFieldInvalid('description')).toBeTrue();
    expect(component.getErrorMessage('description')).toBe('Description is too short');
    
    expect(component.isFieldInvalid('lead')).toBeFalse();
    expect(component.getErrorMessage('lead')).toBe('');
  });
});