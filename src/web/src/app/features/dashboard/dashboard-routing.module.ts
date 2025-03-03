import { NgModule } from '@angular/core'; // v16.2.0
import { RouterModule, Routes } from '@angular/router'; // v16.2.0

import { DashboardPageComponent } from './pages/dashboard-page/dashboard-page.component';

/**
 * Routes configuration for the Dashboard feature module.
 * Defines the available routes within the dashboard feature.
 * Authentication and site-selection guards are applied at the app-routing level.
 */
const routes: Routes = [
  {
    path: '',
    component: DashboardPageComponent,
    // Default dashboard route that displays the main dashboard interface
    // with interaction statistics and summaries for the current site
  }
];

/**
 * Angular module that configures the routes for the dashboard feature
 */
@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class DashboardRoutingModule { }