import { NgModule } from '@angular/core'; // v16.2.0
import { CommonModule } from '@angular/common'; // v16.2.0

import { DashboardRoutingModule } from './dashboard-routing.module';
import { DashboardPageComponent } from './pages/dashboard-page/dashboard-page.component';
import { DashboardService } from './services/dashboard.service';
import { SharedModule } from '../../shared/shared.module';

/**
 * Angular module that bundles all dashboard-related components, services, and routes
 */
@NgModule({ 
  imports: [
    CommonModule,
    SharedModule,
    DashboardRoutingModule
  ],
  declarations: [
    DashboardPageComponent
  ],
  providers: [
    DashboardService
  ]
})
export class DashboardModule { 
  /**
   * Default constructor for the dashboard module
   */
  constructor() { }
}