import { NgModule, ErrorHandler, Optional, SkipSelf, ModuleWithProviders } from '@angular/core'; // v16.2.0
import { CommonModule } from '@angular/common'; // v16.2.0
import { HTTP_INTERCEPTORS, HttpClientModule } from '@angular/common/http'; // v16.2.0

import { AuthModule } from './auth/auth.module';
import { HttpErrorInterceptor } from './errors/http-error.interceptor';
import { GlobalErrorHandler } from './errors/global-error-handler';
import { HttpCacheInterceptor } from './http/http-cache.interceptor';
import { SiteContextInterceptor } from './http/site-context.interceptor';
import { ApiService } from './http/api.service';
import { CacheService } from './cache/cache.service';
import { ErrorHandlerService } from './errors/error-handler.service';
import { AppConfigService } from './config/app-config.service';
import { PerformanceMonitoringService } from './monitoring/performance-monitoring.service';
import { UserActivityService } from './monitoring/user-activity.service';

/**
 * Angular module that serves as the central point for core application services, including
 * HTTP interceptors, authentication, error handling, and cache management.
 * 
 * This module provides the foundation for the entire application, ensuring that essential
 * services are loaded once during application initialization and following the singleton pattern.
 * 
 * The module implements the requirements for User Authentication (F-001), Site-Scoped Access
 * Control (F-002), Error Handling Patterns, and Caching Strategy as specified in the
 * technical documentation.
 */
@NgModule({
  imports: [
    CommonModule,
    HttpClientModule,
    AuthModule
  ],
  providers: [
    // HTTP Interceptors (order matters)
    { 
      provide: HTTP_INTERCEPTORS, 
      useClass: SiteContextInterceptor, 
      multi: true 
    },
    { 
      provide: HTTP_INTERCEPTORS, 
      useClass: HttpCacheInterceptor, 
      multi: true 
    },
    { 
      provide: HTTP_INTERCEPTORS, 
      useClass: HttpErrorInterceptor, 
      multi: true 
    },
    // Custom error handler for application-wide error handling
    { 
      provide: ErrorHandler, 
      useClass: GlobalErrorHandler 
    }
  ]
})
export class CoreModule {
  /**
   * Constructor that prevents multiple instantiation of CoreModule.
   * Throws an error if CoreModule is imported more than once.
   * 
   * @param parentModule Reference to CoreModule if it has already been loaded
   */
  constructor(
    @Optional() @SkipSelf() parentModule: CoreModule | null
  ) {
    if (parentModule) {
      throw new Error(
        'CoreModule is already loaded. Import it in the AppModule only using forRoot().'
      );
    }
  }

  /**
   * Static method to ensure core module is only imported once and to provide configuration.
   * This method registers all singleton services that should exist throughout the application.
   * 
   * @returns ModuleWithProviders object with CoreModule and configured providers
   */
  static forRoot(): ModuleWithProviders<CoreModule> {
    return {
      ngModule: CoreModule,
      providers: [
        // Singleton services
        ApiService,
        CacheService,
        ErrorHandlerService,
        AppConfigService,
        PerformanceMonitoringService,
        UserActivityService
      ]
    };
  }
}