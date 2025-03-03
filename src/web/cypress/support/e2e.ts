/**
 * Main support file for Cypress end-to-end tests in the Interaction Management System.
 * This file configures global behavior, imports custom commands, and sets up the test environment.
 * 
 * @packageDocumentation
 */

// Import Cypress test framework - v12.17.3
import 'cypress';

// Import all custom commands
import './commands';

/**
 * Sets up the Cypress environment for E2E testing with application-specific configuration
 */
function setupE2EEnvironment(): void {
  // Configure Cypress for end-to-end testing
  Cypress.config('viewportWidth', 1280);
  Cypress.config('viewportHeight', 720);
  Cypress.config('defaultCommandTimeout', 5000);
  Cypress.config('testIsolation', true);
  Cypress.config('screenshotOnRunFailure', true);
  
  // Set up global error handling for consistent test behavior
  Cypress.on('uncaught:exception', (err, runnable) => {
    console.error('Uncaught exception:', err.message);
    return false; // Prevent test failure on uncaught exceptions
  });
}

// Run the setup
setupE2EEnvironment();

// Global test hooks
beforeEach(() => {
  // Reset application state before each test to ensure test isolation
  cy.clearLocalStorage();
  cy.clearCookies();
});

afterEach(() => {
  // Perform any necessary cleanup after each test
  // This ensures tests don't affect each other
});