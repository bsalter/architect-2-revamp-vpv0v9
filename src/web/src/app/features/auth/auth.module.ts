import { NgModule } from '@angular/core'; // v16.2.0
import { CommonModule } from '@angular/common'; // v16.2.0
import { ReactiveFormsModule } from '@angular/forms'; // v16.2.0

import { AuthRoutingModule } from './auth-routing.module';
import { SharedModule } from '../../shared/shared.module';
import { LoginComponent } from './components/login/login.component';
import { SiteSelectionComponent } from './components/site-selection/site-selection.component';
import { LoginPageComponent } from './pages/login-page/login-page.component';
import { SiteSelectionPageComponent } from './pages/site-selection-page/site-selection-page.component';
import { AuthPageService } from './services/auth-page.service';

/**
 * Module that configures and organizes all authentication-related components, services, and routing
 */
@NgModule({
  imports: [
    CommonModule,
    ReactiveFormsModule,
    SharedModule,
    AuthRoutingModule
  ],
  declarations: [
    LoginComponent,
    SiteSelectionComponent,
    LoginPageComponent,
    SiteSelectionPageComponent
  ],
  providers: [
    AuthPageService
  ]
})
export class AuthModule { 
  /**
   * Default constructor
   */
  constructor() {
    // Angular creates instance of the module
  }
}