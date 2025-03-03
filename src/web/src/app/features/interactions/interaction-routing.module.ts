import { NgModule } from '@angular/core'; // @angular/core v16.2.0
import { RouterModule, Routes } from '@angular/router'; // @angular/router v16.2.0

import { InteractionFinderPageComponent } from './pages/interaction-finder-page/interaction-finder-page.component';
import { InteractionCreatePageComponent } from './pages/interaction-create-page/interaction-create-page.component';
import { InteractionEditPageComponent } from './pages/interaction-edit-page/interaction-edit-page.component';
import { InteractionViewPageComponent } from './pages/interaction-view-page/interaction-view-page.component';
import { authGuardFn } from '../../core/auth/auth.guard';
import { siteSelectionGuardFn } from '../../core/auth/site-selection.guard';

/**
 * Define the routes for the Interactions feature with appropriate components and guards
 */
const routes: Routes = [
  {
    path: '',
    component: InteractionFinderPageComponent,
    canActivate: [authGuardFn, siteSelectionGuardFn],
    description: 'Default route for the interactions feature showing the finder view'
  },
  {
    path: 'create',
    component: InteractionCreatePageComponent,
    canActivate: [authGuardFn, siteSelectionGuardFn],
    description: 'Route for creating a new interaction'
  },
  {
    path: ':id/edit',
    component: InteractionEditPageComponent,
    canActivate: [authGuardFn, siteSelectionGuardFn],
    description: 'Route for editing an existing interaction with the specified ID'
  },
  {
    path: ':id',
    component: InteractionViewPageComponent,
    canActivate: [authGuardFn, siteSelectionGuardFn],
    description: "Route for viewing an interaction's details with the specified ID"
  }
];

/**
 * Angular module that defines the routing configuration for the Interactions feature
 */
@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class InteractionRoutingModule {
  /**
   * Default constructor
   */
  constructor() {
    // Angular creates instance of the module
  }
}