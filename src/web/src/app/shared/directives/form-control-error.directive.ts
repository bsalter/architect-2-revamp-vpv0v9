import { 
  Directive, 
  ElementRef, 
  Input, 
  OnInit, 
  OnDestroy, 
  ComponentRef, 
  ViewContainerRef, 
  ComponentFactoryResolver 
} from '@angular/core'; // @angular/core version 16.2.0
import { NgControl, AbstractControl } from '@angular/forms'; // @angular/forms version 16.2.0
import { Subscription, fromEvent } from 'rxjs'; // rxjs version 7.8.1
import { debounceTime } from 'rxjs/operators'; // rxjs/operators version 7.8.1

import { ErrorMessageComponent } from '../components/error-message/error-message.component';
import { getFormControlError } from '../../core/utils/form-utils';

/**
 * Directive that automatically displays validation error messages for form controls by dynamically 
 * creating error message components when a control becomes invalid and touched.
 * 
 * Attaches to form controls with formControlName or ngModel directives to provide
 * consistent error message display across the application.
 */
@Directive({
  selector: '[formControlName], [ngModel]'
})
export class FormControlErrorDirective implements OnInit, OnDestroy {
  /**
   * Custom error messages to override the default ones.
   * Should be an object mapping error types to message strings.
   */
  @Input() customErrorMessages: string;
  
  /**
   * Reference to the error message component instance
   */
  private componentRef: ComponentRef<ErrorMessageComponent> = null;
  
  /**
   * Subscription to the control's status changes
   */
  private statusChangeSubscription: Subscription;
  
  /**
   * Subscription to the input's blur event
   */
  private blurSubscription: Subscription;
  
  /**
   * Initializes the directive with necessary dependencies
   * 
   * @param el Reference to the host DOM element
   * @param vcr ViewContainerRef to create dynamic components
   * @param control NgControl to access the form control
   * @param resolver ComponentFactoryResolver to create component instances
   */
  constructor(
    private el: ElementRef,
    private vcr: ViewContainerRef,
    private control: NgControl,
    private resolver: ComponentFactoryResolver
  ) { }
  
  /**
   * Sets up subscriptions to monitor control state changes
   */
  ngOnInit(): void {
    // Subscribe to status changes of the form control
    this.statusChangeSubscription = this.control.statusChanges
      .pipe(debounceTime(100)) // Limit how often we check to avoid performance issues
      .subscribe(() => {
        this.checkErrors();
      });
    
    // Also check errors when the input loses focus
    this.blurSubscription = fromEvent(this.el.nativeElement, 'blur')
      .subscribe(() => {
        this.checkErrors();
      });
  }
  
  /**
   * Cleans up subscriptions and components when directive is destroyed
   */
  ngOnDestroy(): void {
    // Unsubscribe to prevent memory leaks
    if (this.statusChangeSubscription) {
      this.statusChangeSubscription.unsubscribe();
    }
    
    if (this.blurSubscription) {
      this.blurSubscription.unsubscribe();
    }
    
    // Remove the error component if it exists
    this.removeError();
  }
  
  /**
   * Checks if the control has errors and should display them
   */
  private checkErrors(): void {
    if (this.control && this.control.invalid && this.control.touched) {
      this.showError();
    } else {
      this.removeError();
    }
  }
  
  /**
   * Creates and displays the error message component
   */
  private showError(): void {
    // Remove any existing error first
    this.removeError();
    
    // Parse custom error messages if provided as a JSON string
    let parsedMessages: { [key: string]: string } | undefined;
    if (this.customErrorMessages) {
      try {
        parsedMessages = JSON.parse(this.customErrorMessages);
      } catch (e) {
        console.warn('Failed to parse customErrorMessages as JSON:', e);
      }
    }
    
    // Get the appropriate error message for this control
    const errorMessage = getFormControlError(
      this.control.control,
      parsedMessages
    );
    
    // Don't show anything if there's no error message
    if (!errorMessage) {
      return;
    }
    
    // Create the error message component
    const factory = this.resolver.resolveComponentFactory(ErrorMessageComponent);
    this.componentRef = this.vcr.createComponent(factory);
    
    // Configure the component
    this.componentRef.instance.message = errorMessage;
    this.componentRef.instance.type = 'validation';
    
    // Add a class to the host element for styling
    this.el.nativeElement.classList.add('validation-error');
  }
  
  /**
   * Removes the error message component if it exists
   */
  private removeError(): void {
    if (this.componentRef) {
      this.componentRef.destroy();
      this.componentRef = null;
      this.el.nativeElement.classList.remove('validation-error');
    }
  }
}