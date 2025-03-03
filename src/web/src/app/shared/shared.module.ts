import { NgModule } from '@angular/core'; // @angular/core v16.2.0
import { CommonModule } from '@angular/common'; // @angular/common v16.2.0
import { FormsModule, ReactiveFormsModule } from '@angular/forms'; // @angular/forms v16.2.0
import { RouterModule } from '@angular/router'; // @angular/router v16.2.0
import { AgGridModule } from 'ag-grid-angular'; // ag-grid-angular v30.0.3
import { MatButtonModule } from '@angular/material/button'; // @angular/material/button v16.2.0
import { MatCheckboxModule } from '@angular/material/checkbox'; // @angular/material/checkbox v16.2.0
import { MatDatepickerModule } from '@angular/material/datepicker'; // @angular/material/datepicker v16.2.0
import { MatFormFieldModule } from '@angular/material/form-field'; // @angular/material/form-field v16.2.0
import { MatInputModule } from '@angular/material/input'; // @angular/material/input v16.2.0
import { MatRadioModule } from '@angular/material/radio'; // @angular/material/radio v16.2.0
import { MatSelectModule } from '@angular/material/select'; // @angular/material/select v16.2.0
import { MatNativeDateModule } from '@angular/material/core'; // @angular/material/core v16.2.0

import { AlertComponent } from './components/alert/alert.component';
import { BreadcrumbComponent } from './components/breadcrumb/breadcrumb.component';
import { ConfirmationModalComponent } from './components/confirmation-modal/confirmation-modal.component';
import { DateTimePickerComponent } from './components/date-time-picker/date-time-picker.component';
import { ErrorMessageComponent } from './components/error-message/error-message.component';
import { FooterComponent } from './components/footer/footer.component';
import { HeaderComponent } from './components/header/header.component';
import { LoadingIndicatorComponent } from './components/loading-indicator/loading-indicator.component';
import { NavigationComponent } from './components/navigation/navigation.component';
import { PaginationComponent } from './components/pagination/pagination.component';
import { SearchInputComponent } from './components/search-input/search-input.component';
import { ToastComponent } from './components/toast/toast.component';
import { ClickOutsideDirective } from './directives/click-outside.directive';
import { FormControlErrorDirective } from './directives/form-control-error.directive';
import { HasPermissionDirective } from './directives/has-permission.directive';
import { SiteContextDirective } from './directives/site-context.directive';
import { DateFormatPipe } from './pipes/date-format.pipe';
import { FilterPipe } from './pipes/filter.pipe';
import { SafeHtmlPipe } from './pipes/safe-html.pipe';
import { TimezonePipe } from './pipes/timezone.pipe';
import { BreadcrumbService } from './services/breadcrumb.service';
import { ToastService } from './services/toast.service';

/**
 * Angular module that provides shared components, directives, pipes and services across the application
 */
@NgModule({
  declarations: [
    AlertComponent,
    BreadcrumbComponent,
    ConfirmationModalComponent,
    DateTimePickerComponent,
    ErrorMessageComponent,
    FooterComponent,
    HeaderComponent,
    LoadingIndicatorComponent,
    NavigationComponent,
    PaginationComponent,
    SearchInputComponent,
    ToastComponent,
    ClickOutsideDirective,
    FormControlErrorDirective,
    HasPermissionDirective,
    SiteContextDirective,
    DateFormatPipe,
    FilterPipe,
    SafeHtmlPipe,
    TimezonePipe
  ],
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    RouterModule,
    AgGridModule,
    MatButtonModule,
    MatCheckboxModule,
    MatDatepickerModule,
    MatFormFieldModule,
    MatInputModule,
    MatRadioModule,
    MatSelectModule,
    MatNativeDateModule
  ],
  exports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    RouterModule,
    AgGridModule,
    MatButtonModule,
    MatCheckboxModule,
    MatDatepickerModule,
    MatFormFieldModule,
    MatInputModule,
    MatRadioModule,
    MatSelectModule,
    MatNativeDateModule,
    AlertComponent,
    BreadcrumbComponent,
    ConfirmationModalComponent,
    DateTimePickerComponent,
    ErrorMessageComponent,
    FooterComponent,
    HeaderComponent,
    LoadingIndicatorComponent,
    NavigationComponent,
    PaginationComponent,
    SearchInputComponent,
    ToastComponent,
    ClickOutsideDirective,
    FormControlErrorDirective,
    HasPermissionDirective,
    SiteContextDirective,
    DateFormatPipe,
    FilterPipe,
    SafeHtmlPipe,
    TimezonePipe
  ],
  providers: [
    BreadcrumbService,
    ToastService
  ]
})
export class SharedModule {
  /**
   * Default constructor
   */
  constructor() { }
}