import { platformBrowserDynamic } from '@angular/platform-browser-dynamic'; // @angular/platform-browser-dynamic 16.2.0
import { enableProdMode, ErrorHandler } from '@angular/core'; // @angular/core 16.2.0

import { AppModule } from './app/app.module';
import { environment } from './environments/environment';
import { GlobalErrorHandler } from './app/core/errors/global-error-handler';

/**
 * Bootstraps the Angular application with the root module and error handling configuration
 */
async function bootstrapApplication(): Promise<void> {
  // Configure providers array with GlobalErrorHandler
  const providers = [
    { provide: ErrorHandler, useClass: GlobalErrorHandler }
  ];

  try {
    // Call platformBrowserDynamic().bootstrapModule(AppModule)
    await platformBrowserDynamic(providers).bootstrapModule(AppModule);
  } catch (err) {
    // Add catch handler to log bootstrap errors to console
    console.error('Error bootstrapping application:', err);
  }
}

// Conditional check for production environment
if (environment.production) {
  enableProdMode();
}

// Call bootstrapApplication to start the app
bootstrapApplication();