import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing'; // @angular/core/testing v16.2.0
import { ReactiveFormsModule } from '@angular/forms'; // @angular/forms v16.2.0
import { By } from '@angular/platform-browser'; // @angular/platform-browser v16.2.0

import { SearchInputComponent } from './search-input.component';

describe('SearchInputComponent', () => {
  let component: SearchInputComponent;
  let fixture: ComponentFixture<SearchInputComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ReactiveFormsModule],
      declarations: [SearchInputComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(SearchInputComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should set default values for inputs', () => {
    expect(component.placeholder).toEqual('Search interactions...');
    expect(component.debounceTime).toEqual(300);
    expect(component.searchTerm).toEqual('');
  });

  it('should use provided input values', () => {
    // Set input properties
    component.placeholder = 'Custom placeholder';
    component.searchTerm = 'Initial search';
    component.debounceTime = 500;
    
    // Re-initialize component to apply changes
    component.ngOnInit();
    fixture.detectChanges();
    
    // Verify input element has the correct placeholder
    const inputEl = fixture.debugElement.query(By.css('input')).nativeElement;
    expect(inputEl.placeholder).toBe('Custom placeholder');
    
    // Verify search control has the correct value
    expect(component.searchControl.value).toBe('Initial search');
    
    // Other properties can't be visually verified but we can check the component
    expect(component.debounceTime).toBe(500);
  });

  it('should emit search event when input changes', fakeAsync(() => {
    // Create spy on search output
    spyOn(component.search, 'emit');
    
    // Set value of search control
    component.searchControl.setValue('test search');
    
    // Advance time to allow debounce to complete
    tick(300);
    
    // Verify search event was emitted with correct value
    expect(component.search.emit).toHaveBeenCalledWith('test search');
  }));

  it('should emit search event when Enter key is pressed', () => {
    // Create spy on search output
    spyOn(component.search, 'emit');
    
    // Set value of search control
    component.searchControl.setValue('test search');
    
    // Call onSearch method
    component.onSearch();
    
    // Verify search event was emitted
    expect(component.search.emit).toHaveBeenCalledWith('test search');
  });

  it('should clear search and emit cleared event', () => {
    // Set value of search control
    component.searchControl.setValue('test search');
    
    // Create spy on cleared output
    spyOn(component.cleared, 'emit');
    
    // Create mock event
    const mockEvent = new Event('click');
    spyOn(mockEvent, 'stopPropagation');
    
    // Call clearSearch method
    component.clearSearch(mockEvent);
    
    // Verify event propagation was stopped
    expect(mockEvent.stopPropagation).toHaveBeenCalled();
    
    // Verify search control was cleared
    expect(component.searchControl.value).toBe('');
    
    // Verify cleared event was emitted
    expect(component.cleared.emit).toHaveBeenCalled();
  });

  it('should show clear button only when input has value', () => {
    // Initially, search has no value
    fixture.detectChanges();
    
    // Look for clear button (assuming it has a class or attribute that identifies it)
    let clearButton = fixture.debugElement.query(By.css('.clear-button'));
    
    // With no value, expect no clear button
    expect(clearButton).toBeFalsy();
    
    // Set a value in the search control
    component.searchControl.setValue('test search');
    fixture.detectChanges();
    
    // Now look for clear button again
    clearButton = fixture.debugElement.query(By.css('.clear-button'));
    
    // With a value, expect clear button to be present
    expect(clearButton).toBeTruthy();
  });

  it('should handle debounce time correctly', fakeAsync(() => {
    // Set custom debounce time
    component.debounceTime = 500;
    component.ngOnInit(); // Re-initialize to apply new debounce time
    
    // Create spy on search output
    spyOn(component.search, 'emit');
    
    // Set value of search control multiple times quickly
    component.searchControl.setValue('test1');
    tick(100);
    component.searchControl.setValue('test2');
    tick(100);
    component.searchControl.setValue('test3');
    
    // Advance time by less than debounce time
    tick(200);
    
    // Verify search event not emitted yet
    expect(component.search.emit).not.toHaveBeenCalled();
    
    // Advance time to complete debounce period
    tick(200);
    
    // Verify search event emitted once with final value
    expect(component.search.emit).toHaveBeenCalledTimes(1);
    expect(component.search.emit).toHaveBeenCalledWith('test3');
  }));

  it('should unsubscribe on destroy', () => {
    // Create spy on destroy$ subject
    spyOn<any>(component['destroy$'], 'next');
    spyOn<any>(component['destroy$'], 'complete');
    
    // Call ngOnDestroy
    component.ngOnDestroy();
    
    // Verify destroy$ subject was completed
    expect(component['destroy$'].next).toHaveBeenCalled();
    expect(component['destroy$'].complete).toHaveBeenCalled();
  });
});