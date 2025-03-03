/**
 * Configuration file for Cypress component testing with Angular.
 * Sets up the component testing environment and imports necessary utilities
 * for isolated testing of Angular components.
 * 
 * @packageDocumentation
 */

// Import mount function from Cypress Angular adapter - v12.13.0
import { mount } from 'cypress/angular';

// Import Angular modules required for component testing - v16.2.0
import { BrowserModule } from '@angular/platform-browser';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { HttpClientModule } from '@angular/common/http';

// Import custom commands for testing
import './commands';

/**
 * Sets up the Angular testing environment with required modules and providers
 * for component testing.
 */
function setupComponentTestEnvironment(): void {
  // Step 1: Configure Cypress for Angular component testing
  Cypress.on('test:before:run', () => {
    // This runs before each component test
    console.log('Preparing Angular component test environment');
  });

  // Step 2: Set up default Angular testing module with common imports
  const defaultConfig = {
    imports: [
      BrowserModule,
      NoopAnimationsModule,
      HttpClientModule
    ],
    providers: []
  };

  // Step 3: Configure Angular testing environment for isolated component tests
  Cypress.Commands.add('mount', 
    (component, options = {}) => {
      // Merge default configuration with test-specific options
      const mergedConfig = {
        ...defaultConfig,
        ...options,
        imports: [
          ...(defaultConfig.imports || []),
          ...(options.imports || [])
        ],
        providers: [
          ...(defaultConfig.providers || []),
          ...(options.providers || [])
        ]
      };
      
      // Call the original mount with merged configuration
      return mount(component, mergedConfig);
    }
  );
}

// Initialize the component testing environment
setupComponentTestEnvironment();

// Export the mount function for use in Angular component tests
export { mount };