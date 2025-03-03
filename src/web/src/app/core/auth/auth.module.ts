import { NgModule } from '@angular/core'; // v16.2.0
import { CommonModule } from '@angular/common'; // v16.2.0
import { HTTP_INTERCEPTORS } from '@angular/common/http'; // v16.2.0
import { HttpClientModule } from '@angular/common/http'; // v16.2.0

import { AuthService } from './auth.service';
import { TokenService } from './token.service';
import { UserContextService } from './user-context.service';
import { SiteSelectionService } from './site-selection.service';
import { JwtInterceptor } from './jwt-interceptor';
import { AuthGuard, authGuardFn } from './auth.guard';
import { SiteSelectionGuard, siteSelectionGuardFn } from './site-selection.guard';
import { createAuth0Config } from './auth0-config';

/**
 * Angular module that configures authentication services, interceptors and guards for the application.
 * Centralizes all authentication and authorization components to support the authentication framework
 * requirements and site-scoped access control specified in the technical documentation.
 * 
 * This module handles:
 * - JWT token management for secure API communication
 * - HTTP request interception for adding authorization headers
 * - Auth0 integration configuration
 * - Route guards for authentication and site-selection protection
 */
@NgModule({
  imports: [
    CommonModule,
    HttpClientModule
  ],
  providers: [
    // Register JWT interceptor to automatically add authentication tokens to API requests
    {
      provide: HTTP_INTERCEPTORS,
      useClass: JwtInterceptor,
      multi: true
    },
    // Configure Auth0 integration using factory function
    {
      provide: 'Auth0Config',
      useFactory: createAuth0Config
    }
    // Note: AuthService, TokenService, UserContextService, SiteSelectionService, 
    // AuthGuard, and SiteSelectionGuard are provided at the root level via
    // their @Injectable decorators
  ]
})
export class AuthModule { }