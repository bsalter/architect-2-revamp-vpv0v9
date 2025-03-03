import { defineConfig } from 'cypress'; // v12.17.3
import { setupNodeEvents as setupAngularComponentTesting } from '@cypress/angular'; // v2.5.0

/**
 * Setup function for Cypress E2E test events and plugins
 * 
 * @param on - Cypress event registration function
 * @param config - Cypress configuration object
 * @returns Modified configuration object
 */
function setupNodeEvents(on: Cypress.PluginEvents, config: Cypress.PluginConfigOptions): Cypress.PluginConfigOptions {
  // Register plugins for test result collection (useful for CI integration)
  on('after:run', (results) => {
    if (process.env.CI) {
      // Additional CI-specific reporting for GitHub Actions integration
      console.log(`Tests completed with ${results.totalFailed} failures`);
    }
  });
  
  // Configure screenshot and video handling
  on('after:screenshot', (details) => {
    // Process screenshots for reporting
    console.log(`Screenshot taken: ${details.path}`);
    return details;
  });
  
  // Set up custom environment variable handling
  // Allow overriding environment variables from process.env
  const envFromProcess = {
    apiUrl: process.env.CYPRESS_API_URL || config.env.apiUrl,
    auth0Domain: process.env.CYPRESS_AUTH0_DOMAIN || config.env.auth0Domain,
    auth0ClientId: process.env.CYPRESS_AUTH0_CLIENT_ID || config.env.auth0ClientId,
    mockAuth: process.env.CYPRESS_MOCK_AUTH !== undefined 
      ? process.env.CYPRESS_MOCK_AUTH === 'true' 
      : config.env.mockAuth,
  };
  
  // Merge environment variables
  config.env = { ...config.env, ...envFromProcess };
  
  // Register code coverage plugin if enabled
  if (process.env.CYPRESS_COVERAGE === 'true') {
    // Uncomment when adding code coverage package
    // require('@cypress/code-coverage/task')(on, config);
    console.log('Code coverage enabled');
  }
  
  return config;
}

// Export the Cypress configuration
export default defineConfig({
  // End-to-End Testing Configuration
  e2e: {
    baseUrl: 'http://localhost:4200', // Angular application URL
    supportFile: 'cypress/support/e2e.ts',
    specPattern: 'cypress/e2e/**/*.cy.ts',
    fixturesFolder: 'cypress/fixtures',
    viewportWidth: 1280,
    viewportHeight: 720,
    defaultCommandTimeout: 5000,  // 5 seconds for most commands
    responseTimeout: 30000,       // 30 seconds for responses
    video: false,                 // Disable videos by default to save space
    screenshotOnRunFailure: true, // Take screenshots on failure
    chromeWebSecurity: false,     // Allow cross-origin requests during testing
    experimentalStudio: false,    // Disable experimental studio features
    testIsolation: true,          // Test isolation for cleaner tests
    setupNodeEvents,
  },
  
  // Component Testing Configuration
  component: {
    devServer: {
      framework: 'angular',
      bundler: 'webpack',
      options: {
        // Angular project configuration
        projectConfig: {
          root: '',
          sourceRoot: 'src',
          projectType: 'application',
          prefix: 'app',
          architect: {
            build: {
              options: {
                outputPath: 'dist/interaction-management',
                index: 'src/index.html',
                main: 'src/main.ts',
                tsConfig: 'tsconfig.app.json',
              },
            },
          },
        },
      },
    },
    supportFile: 'cypress/support/component.ts',
    specPattern: '**/*.cy.ts',
    indexHtmlFile: 'cypress/support/component-index.html',
    viewportWidth: 500,  // Smaller viewport for component testing
    viewportHeight: 500,
    setupNodeEvents: setupAngularComponentTesting,
  },
  
  // Environment Variables for Testing
  env: {
    // API and authentication settings
    apiUrl: 'http://localhost:5000/api',
    auth0Domain: 'dev-interaction-manager.auth0.com',
    auth0ClientId: 'dev-client-id',
    mockAuth: true,                // Use mock authentication by default in tests
    
    // Test behavior settings
    failOnStatusCode: false,       // Don't fail on non-2xx status codes
    retries: {
      runMode: 2,                  // Retry failed tests up to 2 times in CI mode
      openMode: 0,                 // Don't retry in open mode (interactive)
    },
  },
});