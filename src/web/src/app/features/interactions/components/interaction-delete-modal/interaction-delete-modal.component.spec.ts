import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog'; // @angular/material/dialog v16.2.0
import { NoopAnimationsModule } from '@angular/platform-browser/animations'; // @angular/platform-browser/animations v16.2.0
import { BehaviorSubject, of, throwError } from 'rxjs'; // rxjs v7.8.1

import { InteractionDeleteModalComponent } from './interaction-delete-modal.component';
import { Interaction } from '../../models/interaction.model';
import { InteractionService } from '../../services/interaction.service';

/**
 * Creates a mock interaction object for testing
 * @returns A mock interaction object
 */
function createMockInteraction(): Interaction {
  return {
    id: 123,
    siteId: 1,
    title: 'Project Update Meeting',
    type: 'Meeting',
    lead: 'Jane Smith',
    startDatetime: new Date('2023-06-18T09:15:00Z'),
    endDatetime: new Date('2023-06-18T10:15:00Z'),
    timezone: 'America/New_York',
    location: 'East Wing Room 305',
    description: 'Weekly project status update with team',
    notes: 'Bring the latest metrics',
    createdBy: 1,
    createdAt: new Date('2023-06-10T10:00:00Z'),
    updatedAt: new Date('2023-06-10T10:00:00Z')
  };
}

/**
 * Mock implementation of MatDialogRef for testing
 */
class MockMatDialogRef {
  close = jasmine.createSpy('close');
}

/**
 * Mock implementation of InteractionService for testing
 */
class MockInteractionService {
  deleteInteraction = jasmine.createSpy('deleteInteraction').and.returnValue(of(true));
  loadingSubject = new BehaviorSubject<boolean>(false);
  loading$ = this.loadingSubject.asObservable();
}

describe('InteractionDeleteModalComponent', () => {
  let component: InteractionDeleteModalComponent;
  let fixture: ComponentFixture<InteractionDeleteModalComponent>;
  let mockDialogRef: MockMatDialogRef;
  let mockInteractionService: MockInteractionService;
  let mockInteraction: Interaction;

  beforeEach(() => {
    mockDialogRef = new MockMatDialogRef();
    mockInteractionService = new MockInteractionService();
    mockInteraction = createMockInteraction();

    TestBed.configureTestingModule({
      imports: [NoopAnimationsModule],
      declarations: [InteractionDeleteModalComponent],
      providers: [
        { provide: MatDialogRef, useValue: mockDialogRef },
        { provide: MAT_DIALOG_DATA, useValue: mockInteraction },
        { provide: InteractionService, useValue: mockInteractionService }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(InteractionDeleteModalComponent);
    component = fixture.componentInstance;
    component.interaction = mockInteraction;
    fixture.detectChanges();
  });

  afterEach(() => {
    jasmine.clock().uninstall();
  });

  it('should create the component', () => {
    expect(component).toBeTruthy();
  });

  it('should display the interaction title and formatted date', () => {
    const element = fixture.nativeElement;
    const titleElement = element.querySelector('.modal-title');
    const dateElement = element.querySelector('.interaction-date');
    
    expect(titleElement.textContent).toContain(mockInteraction.title);
    expect(dateElement.textContent).toContain('Jun 18, 2023');
  });

  it('should close the dialog with false when cancel is clicked', () => {
    component.onCancel();
    expect(mockDialogRef.close).toHaveBeenCalledWith(false);
  });

  it('should call deleteInteraction service method when confirm is clicked', () => {
    component.onConfirmDelete();
    expect(mockInteractionService.deleteInteraction).toHaveBeenCalledWith(mockInteraction.id);
  });

  it('should close the dialog with true when deletion is successful', () => {
    mockInteractionService.deleteInteraction.and.returnValue(of(true));
    component.onConfirmDelete();
    expect(mockDialogRef.close).toHaveBeenCalledWith(true);
  });

  it('should handle errors when deletion fails', () => {
    const errorMessage = 'Failed to delete interaction';
    mockInteractionService.deleteInteraction.and.returnValue(throwError(() => new Error(errorMessage)));
    
    component.onConfirmDelete();
    
    expect(component.deleteError).toBe(true);
    expect(component.errorMessage).toContain(errorMessage);
    expect(mockDialogRef.close).not.toHaveBeenCalled();
  });

  it('should display loading state while deletion is in progress', () => {
    // Create a subject to control when the deletion completes
    const deleteSubject = new BehaviorSubject<boolean>(false);
    mockInteractionService.deleteInteraction.and.returnValue(deleteSubject);
    
    // Start deletion process
    component.onConfirmDelete();
    
    // Set loading state to true
    mockInteractionService.loadingSubject.next(true);
    fixture.detectChanges();
    
    // Verify loading state is displayed
    expect(component.isDeleting).toBe(true);
    const loadingElement = fixture.nativeElement.querySelector('.loading-indicator');
    expect(loadingElement).toBeTruthy();
    
    // Complete the deletion and check state updates
    mockInteractionService.loadingSubject.next(false);
    deleteSubject.next(true);
    deleteSubject.complete();
    fixture.detectChanges();
    
    expect(component.isDeleting).toBe(false);
  });

  it('should format the date correctly with timezone', () => {
    // Spy on the formatDateTimeWithTimezone function
    spyOn(component as any, 'formatDate').and.callThrough();
    
    // Initialize component to trigger date formatting
    component.ngOnInit();
    
    // Verify the formatting uses timezone
    expect((component as any).formatDate).toHaveBeenCalledWith(
      mockInteraction.startDatetime,
      jasmine.anything()
    );
    expect(component.formattedDate).toContain('2023');
  });

  it('should display error message when deletion fails', () => {
    // Set up error state
    const errorMessage = 'Network error occurred';
    mockInteractionService.deleteInteraction.and.returnValue(throwError(() => new Error(errorMessage)));
    
    // Trigger deletion
    component.onConfirmDelete();
    fixture.detectChanges();
    
    // Check if error message is displayed
    const errorElement = fixture.nativeElement.querySelector('.error-message');
    expect(errorElement).toBeTruthy();
    expect(errorElement.textContent).toContain(errorMessage);
  });

  it('should clean up subscriptions when destroyed', () => {
    // Spy on the unsubscribe method for destroy$ subject
    const destroySpy = spyOn(component['destroy$'], 'next').and.callThrough();
    const completeSpy = spyOn(component['destroy$'], 'complete').and.callThrough();
    
    // Mock loadingSubscription
    const mockSubscription = jasmine.createSpyObj('Subscription', ['unsubscribe']);
    component['loadingSubscription'] = mockSubscription;
    
    // Call ngOnDestroy
    component.ngOnDestroy();
    
    // Verify cleanup
    expect(destroySpy).toHaveBeenCalled();
    expect(completeSpy).toHaveBeenCalled();
    expect(mockSubscription.unsubscribe).toHaveBeenCalled();
  });
});