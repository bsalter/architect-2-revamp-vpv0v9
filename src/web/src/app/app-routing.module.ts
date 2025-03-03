import { NgModule } from '@angular/core'; // @angular/core 16.2.0
import { RouterModule, Routes, PreloadAllModules } from '@angular/router'; // @angular/router 16.2.0
import { authGuardFn } from './core/auth/auth.guard';
import { siteSelectionGuardFn } from './core/auth/site-selection.guard';

/**
 * Main application routes configuration
 * Defines the routing structure for the entire application with appropriate guards
 * and lazy loading of feature modules for optimized loading performance.
 */
const routes: Routes = [
  {
    path: 'auth',
    loadChildren: () => import('./features/auth/auth.module').then(m => m.AuthModule),
    description: 'Lazy loaded Authentication feature module'
  },
  {
    path: 'dashboard',
    loadChildren: () => import('./features/dashboard/dashboard.module').then(m => m.DashboardModule),
    canActivate: [authGuardFn, siteSelectionGuardFn],
    description: 'Lazy loaded Dashboard feature module protected by authentication and site selection guards'
  },
  {
    path: 'interactions',
    loadChildren: () => import('./features/interactions/interaction.module').then(m => m.InteractionModule),
    canActivate: [authGuardFn, siteSelectionGuardFn],
    description: 'Lazy loaded Interactions feature module protected by authentication and site selection guards'
  },
  {
    path: '',
    redirectTo: 'dashboard',
    pathMatch: 'full',
    description: 'Default route redirects to the dashboard'
  },
  {
    path: '**',
    redirectTo: 'dashboard',
    description: 'Wildcard route for handling undefined routes, redirects to dashboard'
  }
];

/**
 * Angular module that configures the application's root routing with lazy-loaded feature modules and route guards
 */
@NgModule({
  imports: [
    RouterModule.forRoot(routes, {
      preloadingStrategy: PreloadAllModules, // Preload all modules in the background after initial load
      initialNavigation: 'enabledBlocking' // Enable blocking initial navigation for proper SSR support
    })
  ],
  exports: [RouterModule]
})
export class AppRoutingModule { }