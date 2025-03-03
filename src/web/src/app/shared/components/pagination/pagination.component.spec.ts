import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing'; // Angular 16.2.0
import { By } from '@angular/platform-browser'; // Angular 16.2.0
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome'; // 0.13.0
import { PaginationComponent } from './pagination.component';

/**
 * Utility function to create and initialize the component for testing
 */
async function createTestComponent(): Promise<void> {
  await TestBed.configureTestingModule({
    imports: [FontAwesomeModule],
    declarations: [PaginationComponent]
  }).compileComponents();
}

describe('PaginationComponent', () => {
  let fixture: ComponentFixture<PaginationComponent>;
  let component: PaginationComponent;

  beforeEach(async () => {
    await createTestComponent();
    fixture = TestBed.createComponent(PaginationComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create the component', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize with default values', () => {
    expect(component.currentPage).toBe(1);
    expect(component.totalPages).toBe(1);
    expect(component.maxVisiblePages).toBe(5);
    expect(component.visiblePages).toEqual([1]);
    expect(component.showStartEllipsis).toBeFalsy();
    expect(component.showEndEllipsis).toBeFalsy();
  });

  it('should calculate visible pages correctly with few pages', () => {
    component.totalPages = 3;
    component.currentPage = 2;
    component.ngOnChanges({
      totalPages: {
        currentValue: 3,
        previousValue: undefined,
        firstChange: true,
        isFirstChange: () => true
      },
      currentPage: {
        currentValue: 2,
        previousValue: undefined,
        firstChange: true,
        isFirstChange: () => true
      }
    });
    fixture.detectChanges();

    expect(component.visiblePages).toEqual([1, 2, 3]);
    expect(component.showStartEllipsis).toBeFalsy();
    expect(component.showEndEllipsis).toBeFalsy();
  });

  it('should calculate visible pages correctly with many pages', () => {
    component.totalPages = 10;
    component.currentPage = 5;
    component.ngOnChanges({
      totalPages: {
        currentValue: 10,
        previousValue: undefined,
        firstChange: true,
        isFirstChange: () => true
      },
      currentPage: {
        currentValue: 5,
        previousValue: undefined,
        firstChange: true,
        isFirstChange: () => true
      }
    });
    fixture.detectChanges();

    // Should show pages around the current page with ellipsis on both sides
    expect(component.visiblePages).toContain(3);
    expect(component.visiblePages).toContain(4);
    expect(component.visiblePages).toContain(5);
    expect(component.visiblePages).toContain(6);
    expect(component.visiblePages).toContain(7);
    expect(component.showStartEllipsis).toBeTruthy();
    expect(component.showEndEllipsis).toBeTruthy();
  });

  it('should handle start of pagination range correctly', () => {
    component.totalPages = 10;
    component.currentPage = 1;
    component.ngOnChanges({
      totalPages: {
        currentValue: 10,
        previousValue: undefined,
        firstChange: true,
        isFirstChange: () => true
      },
      currentPage: {
        currentValue: 1,
        previousValue: undefined,
        firstChange: true,
        isFirstChange: () => true
      }
    });
    fixture.detectChanges();

    // Should not show start ellipsis when at the beginning
    expect(component.showStartEllipsis).toBeFalsy();
    expect(component.showEndEllipsis).toBeTruthy();
    expect(component.visiblePages[0]).toBe(1);
  });

  it('should handle end of pagination range correctly', () => {
    component.totalPages = 10;
    component.currentPage = 10;
    component.ngOnChanges({
      totalPages: {
        currentValue: 10,
        previousValue: undefined,
        firstChange: true,
        isFirstChange: () => true
      },
      currentPage: {
        currentValue: 10,
        previousValue: undefined,
        firstChange: true,
        isFirstChange: () => true
      }
    });
    fixture.detectChanges();

    // Should not show end ellipsis when at the end
    expect(component.showStartEllipsis).toBeTruthy();
    expect(component.showEndEllipsis).toBeFalsy();
    expect(component.visiblePages[component.visiblePages.length - 1]).toBe(10);
  });

  it('should emit pageChange event when valid page is selected', () => {
    const pageChangeSpy = spyOn(component.pageChange, 'emit');
    component.currentPage = 2;
    component.totalPages = 5;
    component.ngOnChanges({
      totalPages: {
        currentValue: 5,
        previousValue: undefined,
        firstChange: true,
        isFirstChange: () => true
      },
      currentPage: {
        currentValue: 2,
        previousValue: undefined,
        firstChange: true,
        isFirstChange: () => true
      }
    });
    fixture.detectChanges();

    component.goToPage(3);
    expect(pageChangeSpy).toHaveBeenCalledWith(3);
  });

  it('should not emit pageChange event for invalid pages', () => {
    const pageChangeSpy = spyOn(component.pageChange, 'emit');
    component.currentPage = 2;
    component.totalPages = 5;
    component.ngOnChanges({
      totalPages: {
        currentValue: 5,
        previousValue: undefined,
        firstChange: true,
        isFirstChange: () => true
      },
      currentPage: {
        currentValue: 2,
        previousValue: undefined,
        firstChange: true,
        isFirstChange: () => true
      }
    });
    fixture.detectChanges();

    // These should not emit the event
    component.goToPage(0); // Invalid - below min
    component.goToPage(6); // Invalid - above max
    component.goToPage(null); // Invalid - not a number
    
    expect(pageChangeSpy).not.toHaveBeenCalled();
  });

  it('should not emit pageChange when clicking the current page', () => {
    const pageChangeSpy = spyOn(component.pageChange, 'emit');
    component.currentPage = 3;
    component.totalPages = 5;
    component.ngOnChanges({
      totalPages: {
        currentValue: 5,
        previousValue: undefined,
        firstChange: true,
        isFirstChange: () => true
      },
      currentPage: {
        currentValue: 3,
        previousValue: undefined,
        firstChange: true,
        isFirstChange: () => true
      }
    });
    fixture.detectChanges();

    component.goToPage(3); // Current page
    expect(pageChangeSpy).not.toHaveBeenCalled();
  });

  it('should properly validate page numbers', () => {
    component.totalPages = 5;
    
    // Test current page validation
    component.currentPage = 1;
    expect(component.isCurrentPageValid()).toBeTruthy();
    
    component.currentPage = 5;
    expect(component.isCurrentPageValid()).toBeTruthy();
    
    component.currentPage = 0;
    expect(component.isCurrentPageValid()).toBeFalsy();
    
    component.currentPage = 6;
    expect(component.isCurrentPageValid()).toBeFalsy();
    
    component.currentPage = null;
    expect(component.isCurrentPageValid()).toBeFalsy();
    
    component.currentPage = undefined;
    expect(component.isCurrentPageValid()).toBeFalsy();
    
    component.currentPage = '3' as any;
    expect(component.isCurrentPageValid()).toBeFalsy();
  });

  it('should display the correct number of page buttons', () => {
    component.totalPages = 7;
    component.currentPage = 4;
    component.maxVisiblePages = 5;
    component.ngOnChanges({
      totalPages: {
        currentValue: 7,
        previousValue: undefined,
        firstChange: true,
        isFirstChange: () => true
      },
      currentPage: {
        currentValue: 4,
        previousValue: undefined,
        firstChange: true,
        isFirstChange: () => true
      },
      maxVisiblePages: {
        currentValue: 5,
        previousValue: undefined,
        firstChange: true,
        isFirstChange: () => true
      }
    });
    fixture.detectChanges();

    const pageButtons = fixture.debugElement.queryAll(By.css('.page-button'));
    expect(pageButtons.length).toBe(5); // Should match maxVisiblePages
  });

  it('should disable previous and first buttons on first page', () => {
    component.totalPages = 5;
    component.currentPage = 1;
    component.ngOnChanges({
      totalPages: {
        currentValue: 5,
        previousValue: undefined,
        firstChange: true,
        isFirstChange: () => true
      },
      currentPage: {
        currentValue: 1,
        previousValue: undefined,
        firstChange: true,
        isFirstChange: () => true
      }
    });
    fixture.detectChanges();

    const firstButton = fixture.debugElement.query(By.css('.first-page-button'));
    const prevButton = fixture.debugElement.query(By.css('.prev-page-button'));
    const nextButton = fixture.debugElement.query(By.css('.next-page-button'));
    const lastButton = fixture.debugElement.query(By.css('.last-page-button'));

    expect(firstButton.nativeElement.disabled).toBeTruthy();
    expect(prevButton.nativeElement.disabled).toBeTruthy();
    expect(nextButton.nativeElement.disabled).toBeFalsy();
    expect(lastButton.nativeElement.disabled).toBeFalsy();
  });

  it('should disable next and last buttons on last page', () => {
    component.totalPages = 5;
    component.currentPage = 5;
    component.ngOnChanges({
      totalPages: {
        currentValue: 5,
        previousValue: undefined,
        firstChange: true,
        isFirstChange: () => true
      },
      currentPage: {
        currentValue: 5,
        previousValue: undefined,
        firstChange: true,
        isFirstChange: () => true
      }
    });
    fixture.detectChanges();

    const firstButton = fixture.debugElement.query(By.css('.first-page-button'));
    const prevButton = fixture.debugElement.query(By.css('.prev-page-button'));
    const nextButton = fixture.debugElement.query(By.css('.next-page-button'));
    const lastButton = fixture.debugElement.query(By.css('.last-page-button'));

    expect(firstButton.nativeElement.disabled).toBeFalsy();
    expect(prevButton.nativeElement.disabled).toBeFalsy();
    expect(nextButton.nativeElement.disabled).toBeTruthy();
    expect(lastButton.nativeElement.disabled).toBeTruthy();
  });

  it('should navigate to first page when first button is clicked', () => {
    const pageChangeSpy = spyOn(component.pageChange, 'emit');
    component.totalPages = 10;
    component.currentPage = 5;
    component.ngOnChanges({
      totalPages: {
        currentValue: 10,
        previousValue: undefined,
        firstChange: true,
        isFirstChange: () => true
      },
      currentPage: {
        currentValue: 5,
        previousValue: undefined,
        firstChange: true,
        isFirstChange: () => true
      }
    });
    fixture.detectChanges();

    const firstButton = fixture.debugElement.query(By.css('.first-page-button'));
    firstButton.nativeElement.click();
    
    expect(pageChangeSpy).toHaveBeenCalledWith(1);
  });

  it('should navigate to previous page when previous button is clicked', () => {
    const pageChangeSpy = spyOn(component.pageChange, 'emit');
    component.totalPages = 10;
    component.currentPage = 5;
    component.ngOnChanges({
      totalPages: {
        currentValue: 10,
        previousValue: undefined,
        firstChange: true,
        isFirstChange: () => true
      },
      currentPage: {
        currentValue: 5,
        previousValue: undefined,
        firstChange: true,
        isFirstChange: () => true
      }
    });
    fixture.detectChanges();

    const prevButton = fixture.debugElement.query(By.css('.prev-page-button'));
    prevButton.nativeElement.click();
    
    expect(pageChangeSpy).toHaveBeenCalledWith(4);
  });

  it('should navigate to next page when next button is clicked', () => {
    const pageChangeSpy = spyOn(component.pageChange, 'emit');
    component.totalPages = 10;
    component.currentPage = 5;
    component.ngOnChanges({
      totalPages: {
        currentValue: 10,
        previousValue: undefined,
        firstChange: true,
        isFirstChange: () => true
      },
      currentPage: {
        currentValue: 5,
        previousValue: undefined,
        firstChange: true,
        isFirstChange: () => true
      }
    });
    fixture.detectChanges();

    const nextButton = fixture.debugElement.query(By.css('.next-page-button'));
    nextButton.nativeElement.click();
    
    expect(pageChangeSpy).toHaveBeenCalledWith(6);
  });

  it('should navigate to last page when last button is clicked', () => {
    const pageChangeSpy = spyOn(component.pageChange, 'emit');
    component.totalPages = 10;
    component.currentPage = 5;
    component.ngOnChanges({
      totalPages: {
        currentValue: 10,
        previousValue: undefined,
        firstChange: true,
        isFirstChange: () => true
      },
      currentPage: {
        currentValue: 5,
        previousValue: undefined,
        firstChange: true,
        isFirstChange: () => true
      }
    });
    fixture.detectChanges();

    const lastButton = fixture.debugElement.query(By.css('.last-page-button'));
    lastButton.nativeElement.click();
    
    expect(pageChangeSpy).toHaveBeenCalledWith(10);
  });

  it('should recalculate pages when inputs change', () => {
    const calculateVisiblePagesSpy = spyOn(component, 'calculateVisiblePages').and.callThrough();
    
    component.totalPages = 5;
    component.currentPage = 3;
    component.ngOnChanges({
      totalPages: {
        currentValue: 5,
        previousValue: undefined,
        firstChange: true,
        isFirstChange: () => true
      },
      currentPage: {
        currentValue: 3,
        previousValue: undefined,
        firstChange: true,
        isFirstChange: () => true
      }
    });
    
    expect(calculateVisiblePagesSpy).toHaveBeenCalled();
    calculateVisiblePagesSpy.calls.reset();
    
    component.totalPages = 10;
    component.ngOnChanges({
      totalPages: {
        currentValue: 10,
        previousValue: 5,
        firstChange: false,
        isFirstChange: () => false
      }
    });
    
    expect(calculateVisiblePagesSpy).toHaveBeenCalled();
  });

  it('should handle ellipsis display correctly', () => {
    component.totalPages = 20;
    component.currentPage = 10;
    component.ngOnChanges({
      totalPages: {
        currentValue: 20,
        previousValue: undefined,
        firstChange: true,
        isFirstChange: () => true
      },
      currentPage: {
        currentValue: 10,
        previousValue: undefined,
        firstChange: true,
        isFirstChange: () => true
      }
    });
    fixture.detectChanges();

    const ellipsisElements = fixture.debugElement.queryAll(By.css('.page-ellipsis'));
    expect(ellipsisElements.length).toBe(2); // Both start and end ellipsis
  });

  it('should adjust visible pages when maxVisiblePages changes', () => {
    component.totalPages = 10;
    component.currentPage = 5;
    component.maxVisiblePages = 3;
    component.ngOnChanges({
      totalPages: {
        currentValue: 10,
        previousValue: undefined,
        firstChange: true,
        isFirstChange: () => true
      },
      currentPage: {
        currentValue: 5,
        previousValue: undefined,
        firstChange: true,
        isFirstChange: () => true
      },
      maxVisiblePages: {
        currentValue: 3,
        previousValue: undefined,
        firstChange: true,
        isFirstChange: () => true
      }
    });
    fixture.detectChanges();
    
    expect(component.visiblePages.length).toBe(3);
    
    component.maxVisiblePages = 7;
    component.ngOnChanges({
      maxVisiblePages: {
        currentValue: 7,
        previousValue: 3,
        firstChange: false,
        isFirstChange: () => false
      }
    });
    fixture.detectChanges();
    
    expect(component.visiblePages.length).toBe(7);
  });

  it('should handle accessibility attributes correctly', () => {
    component.totalPages = 5;
    component.currentPage = 3;
    component.ngOnChanges({
      totalPages: {
        currentValue: 5,
        previousValue: undefined,
        firstChange: true,
        isFirstChange: () => true
      },
      currentPage: {
        currentValue: 3,
        previousValue: undefined,
        firstChange: true,
        isFirstChange: () => true
      }
    });
    fixture.detectChanges();

    const navElement = fixture.debugElement.query(By.css('nav'));
    expect(navElement.attributes['aria-label']).toBe('Pagination');
    
    const currentPageButton = fixture.debugElement.queryAll(By.css('.page-button'))
      .find(button => button.nativeElement.textContent.trim() === '3'); // Current page is 3
    
    expect(currentPageButton.attributes['aria-current']).toBe('page');
    
    const firstButton = fixture.debugElement.query(By.css('.first-page-button'));
    const prevButton = fixture.debugElement.query(By.css('.prev-page-button'));
    const nextButton = fixture.debugElement.query(By.css('.next-page-button'));
    const lastButton = fixture.debugElement.query(By.css('.last-page-button'));
    
    expect(firstButton.attributes['aria-label']).toBe('Go to first page');
    expect(prevButton.attributes['aria-label']).toBe('Go to previous page');
    expect(nextButton.attributes['aria-label']).toBe('Go to next page');
    expect(lastButton.attributes['aria-label']).toBe('Go to last page');
  });
});