import { NgModule } from '@angular/core'; // v16.2.0
import { RouterModule, Routes } from '@angular/router'; // v16.2.0

import { LoginPageComponent } from './pages/login-page/login-page.component';
import { SiteSelectionPageComponent } from './pages/site-selection-page/site-selection-page.component';
import { authGuardFn } from '../../core/auth/auth.guard';

/**
 * Routes configuration for the authentication feature module.
 * Defines paths for login, Auth0 callback handling, and site selection.
 */
const routes: Routes = [
  {
    path: 'login',
    component: LoginPageComponent,
    description: 'Route for the login page'
  },
  {
    path: 'callback',
    component: LoginPageComponent,
    description: 'Route for handling Auth0 authentication callback'
  },
  {
    path: 'site-selection',
    component: SiteSelectionPageComponent,
    canActivate: [authGuardFn],
    description: 'Route for the site selection page'
  },
  {
    path: '',
    redirectTo: 'login',
    pathMatch: 'full',
    description: 'Default route for the auth module redirects to login'
  }
];

/**
 * Authentication routing module that defines all authentication-related routes.
 * This module is imported by the auth.module.ts to provide routing functionality.
 */
@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class AuthRoutingModule { }