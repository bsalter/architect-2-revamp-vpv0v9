/**
 * Custom Cypress commands for end-to-end testing of the Interaction Management System.
 * This file provides commands for authentication, site selection, interaction management,
 * and common UI operations to support comprehensive testing.
 * 
 * @packageDocumentation
 */

// Import Cypress - v12.17.3
import 'cypress';

// Type definitions for command parameters
interface LoginOptions {
  username: string;
  password: string;
  rememberMe?: boolean;
}

interface InteractionData {
  title: string;
  type: string;
  lead: string;
  startDatetime: string;
  endDatetime: string;
  timezone: string;
  location?: string;
  description: string;
  notes?: string;
}

// Declare global namespace extension for TypeScript
declare global {
  namespace Cypress {
    interface Chainable {
      // Authentication commands
      login(username: string, password: string, options?: LoginOptions): Chainable<Element>;
      logout(): Chainable<Element>;
      checkAuthState(expectedState: 'authenticated' | 'unauthenticated'): Chainable<Element>;
      
      // Site commands
      selectSite(siteId: number): Chainable<Element>;
      getUserSites(): Chainable<Element>;
      checkCurrentSite(expectedSiteId: number): Chainable<Element>;
      
      // Interaction commands
      createInteraction(data: InteractionData): Chainable<Element>;
      editInteraction(interactionId: number, data: Partial<InteractionData>): Chainable<Element>;
      deleteInteraction(interactionId: number): Chainable<Element>;
      viewInteractionDetails(interactionId: number): Chainable<Element>;
      searchInteractions(searchTerm: string): Chainable<Element>;
      
      // UI commands
      waitForAngular(): Chainable<Element>;
      fillFormField(fieldName: string, value: string | number | boolean): Chainable<Element>;
      checkFormValidation(fieldName: string, expectedState: 'valid' | 'invalid'): Chainable<Element>;
      checkTableData(expectedData: Array<Record<string, any>>): Chainable<Element>;
    }
  }
}

/**
 * Registers authentication-related Cypress commands
 */
function registerAuthCommands(): void {
  // Login command - mocks Auth0 authentication flow
  Cypress.Commands.add('login', (username: string, password: string, options?: LoginOptions) => {
    // Mock Auth0 authentication response
    cy.intercept('POST', '**/oauth/token', {
      statusCode: 200,
      body: {
        access_token: 'mock-jwt-token',
        expires_in: 86400,
        token_type: 'Bearer',
        id_token: 'mock-id-token'
      }
    }).as('authLogin');
    
    // Set localStorage to simulate authenticated state
    cy.window().then(win => {
      win.localStorage.setItem('auth_token', 'mock-jwt-token');
      win.localStorage.setItem('auth_expires_at', (Date.now() + 86400 * 1000).toString());
      win.localStorage.setItem('user', JSON.stringify({
        sub: 'test-user-id',
        name: username,
        email: `${username}@example.com`,
        sites: [1, 2, 3] // Mock user has access to these sites
      }));
    });
    
    // Force reload to apply authentication state
    cy.visit('/');
    
    // Verify authentication is successful
    cy.waitForAngular();
    cy.get('[data-testid="user-profile"]').should('exist');
  });
  
  // Logout command - clears authentication state
  Cypress.Commands.add('logout', () => {
    // Clear authentication data
    cy.window().then(win => {
      win.localStorage.removeItem('auth_token');
      win.localStorage.removeItem('auth_expires_at');
      win.localStorage.removeItem('user');
      win.localStorage.removeItem('selected_site');
    });
    
    // Clear cookies and reload
    cy.clearCookies();
    cy.visit('/');
    
    // Verify logout is successful
    cy.waitForAngular();
    cy.get('[data-testid="login-form"]').should('exist');
  });
  
  // Check authentication state
  Cypress.Commands.add('checkAuthState', (expectedState: 'authenticated' | 'unauthenticated') => {
    cy.waitForAngular();
    
    if (expectedState === 'authenticated') {
      // Check for authenticated elements
      cy.get('[data-testid="user-profile"]').should('exist');
    } else {
      // Check for login form
      cy.get('[data-testid="login-form"]').should('exist');
    }
  });
}

/**
 * Registers site selection and management Cypress commands
 */
function registerSiteCommands(): void {
  // Select site command
  Cypress.Commands.add('selectSite', (siteId: number) => {
    // Check if user is logged in
    cy.window().then(win => {
      const authToken = win.localStorage.getItem('auth_token');
      if (!authToken) {
        throw new Error('User must be logged in before selecting a site');
      }
      
      // Set the selected site in localStorage
      win.localStorage.setItem('selected_site', siteId.toString());
      
      // Intercept site access API call
      cy.intercept('GET', '**/api/sites/' + siteId, {
        statusCode: 200,
        body: {
          id: siteId,
          name: 'Test Site ' + siteId,
          description: 'This is a test site'
        }
      }).as('getSite');
      
      // Navigate to refresh site context
      cy.visit('/');
      cy.wait('@getSite');
      cy.waitForAngular();
    });
  });
  
  // Get user sites command
  Cypress.Commands.add('getUserSites', () => {
    cy.intercept('GET', '**/api/users/sites', {
      statusCode: 200,
      body: [
        { id: 1, name: 'Headquarters', description: 'Main office location' },
        { id: 2, name: 'Northwest Regional Office', description: 'Regional branch' },
        { id: 3, name: 'Southwest Regional Office', description: 'Regional branch' }
      ]
    }).as('getUserSites');
    
    // Navigate to site selection page
    cy.visit('/select-site');
    cy.wait('@getUserSites');
    cy.waitForAngular();
  });
  
  // Check current site
  Cypress.Commands.add('checkCurrentSite', (expectedSiteId: number) => {
    cy.window().then(win => {
      const selectedSite = win.localStorage.getItem('selected_site');
      expect(selectedSite).to.eq(expectedSiteId.toString());
    });
    
    // Also verify site is displayed in UI
    cy.get('[data-testid="current-site"]').should('contain', 'Site ' + expectedSiteId);
  });
}

/**
 * Registers interaction management Cypress commands
 */
function registerInteractionCommands(): void {
  // Create interaction command
  Cypress.Commands.add('createInteraction', (data: InteractionData) => {
    // Intercept the creation API call
    cy.intercept('POST', '**/api/interactions', {
      statusCode: 201,
      body: {
        id: 100, // Mock ID for the new interaction
        ...data,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      }
    }).as('createInteraction');
    
    // Navigate to create form
    cy.visit('/interactions/new');
    cy.waitForAngular();
    
    // Fill form fields
    cy.fillFormField('title', data.title);
    cy.fillFormField('type', data.type);
    cy.fillFormField('lead', data.lead);
    cy.fillFormField('startDatetime', data.startDatetime);
    cy.fillFormField('endDatetime', data.endDatetime);
    cy.fillFormField('timezone', data.timezone);
    if (data.location) {
      cy.fillFormField('location', data.location);
    }
    cy.fillFormField('description', data.description);
    if (data.notes) {
      cy.fillFormField('notes', data.notes);
    }
    
    // Submit the form
    cy.get('[data-testid="save-interaction-btn"]').click();
    cy.wait('@createInteraction');
    
    // Verify we're redirected to the finder view
    cy.url().should('include', '/interactions');
  });
  
  // Edit interaction command
  Cypress.Commands.add('editInteraction', (interactionId: number, data: Partial<InteractionData>) => {
    // Intercept the get interaction API call
    cy.intercept('GET', `**/api/interactions/${interactionId}`, {
      statusCode: 200,
      body: {
        id: interactionId,
        title: 'Original Title',
        type: 'Meeting',
        lead: 'J. Smith',
        startDatetime: '2023-06-15T10:00:00Z',
        endDatetime: '2023-06-15T11:00:00Z',
        timezone: 'America/New_York',
        location: 'Conference Room A',
        description: 'Original description',
        notes: 'Original notes',
        createdAt: '2023-06-10T10:00:00Z',
        updatedAt: '2023-06-10T10:00:00Z'
      }
    }).as('getInteraction');
    
    // Intercept the update API call
    cy.intercept('PUT', `**/api/interactions/${interactionId}`, {
      statusCode: 200,
      body: {
        id: interactionId,
        ...data,
        updatedAt: new Date().toISOString()
      }
    }).as('updateInteraction');
    
    // Navigate to edit form
    cy.visit(`/interactions/${interactionId}/edit`);
    cy.wait('@getInteraction');
    cy.waitForAngular();
    
    // Update form fields based on provided data
    Object.entries(data).forEach(([key, value]) => {
      if (value !== undefined) {
        cy.fillFormField(key, value);
      }
    });
    
    // Submit the form
    cy.get('[data-testid="save-interaction-btn"]').click();
    cy.wait('@updateInteraction');
    
    // Verify we're redirected to the finder view
    cy.url().should('include', '/interactions');
  });
  
  // Delete interaction command
  Cypress.Commands.add('deleteInteraction', (interactionId: number) => {
    // Intercept the delete API call
    cy.intercept('DELETE', `**/api/interactions/${interactionId}`, {
      statusCode: 200,
      body: {
        success: true
      }
    }).as('deleteInteraction');
    
    // Navigate to interaction details
    cy.visit(`/interactions/${interactionId}`);
    cy.waitForAngular();
    
    // Click delete button and confirm
    cy.get('[data-testid="delete-interaction-btn"]').click();
    cy.get('[data-testid="confirm-delete-btn"]').click();
    
    cy.wait('@deleteInteraction');
    
    // Verify we're redirected to the finder view
    cy.url().should('include', '/interactions');
  });
  
  // View interaction details command
  Cypress.Commands.add('viewInteractionDetails', (interactionId: number) => {
    // Intercept the get interaction API call
    cy.intercept('GET', `**/api/interactions/${interactionId}`, {
      statusCode: 200,
      body: {
        id: interactionId,
        title: 'Test Interaction',
        type: 'Meeting',
        lead: 'J. Smith',
        startDatetime: '2023-06-15T10:00:00Z',
        endDatetime: '2023-06-15T11:00:00Z',
        timezone: 'America/New_York',
        location: 'Conference Room A',
        description: 'Test description',
        notes: 'Test notes',
        createdAt: '2023-06-10T10:00:00Z',
        updatedAt: '2023-06-10T10:00:00Z'
      }
    }).as('getInteraction');
    
    // Navigate to interaction details
    cy.visit(`/interactions/${interactionId}`);
    cy.wait('@getInteraction');
    cy.waitForAngular();
    
    // Verify page title contains interaction title
    cy.get('h1').should('contain', 'Test Interaction');
  });
  
  // Search interactions command
  Cypress.Commands.add('searchInteractions', (searchTerm: string) => {
    // Intercept the search API call
    cy.intercept('GET', `**/api/search/interactions?*`, {
      statusCode: 200,
      body: {
        results: [
          { 
            id: 1, 
            title: 'Result 1 ' + searchTerm, 
            type: 'Meeting',
            lead: 'J. Smith',
            startDatetime: '2023-06-15T10:00:00Z',
            endDatetime: '2023-06-15T11:00:00Z',
            timezone: 'America/New_York',
            location: 'Conference Room A'
          },
          { 
            id: 2, 
            title: 'Result 2 ' + searchTerm, 
            type: 'Call',
            lead: 'M. Jones',
            startDatetime: '2023-06-16T14:30:00Z',
            endDatetime: '2023-06-16T15:30:00Z',
            timezone: 'America/New_York',
            location: 'Virtual'
          }
        ],
        total: 2,
        page: 1
      }
    }).as('searchInteractions');
    
    // Navigate to interactions page
    cy.visit('/interactions');
    cy.waitForAngular();
    
    // Enter search term
    cy.get('[data-testid="search-input"]').clear().type(searchTerm);
    cy.get('[data-testid="search-input"]').type('{enter}');
    
    cy.wait('@searchInteractions');
    
    // Verify results are displayed
    cy.get('[data-testid="interaction-table"]').should('exist');
    cy.get('[data-testid="interaction-row"]').should('have.length', 2);
  });
}

/**
 * Registers UI interaction Cypress commands
 */
function registerUICommands(): void {
  // Wait for Angular
  Cypress.Commands.add('waitForAngular', () => {
    cy.window().then(win => {
      // Check for Angular loading to complete
      return new Cypress.Promise((resolve) => {
        if (win.getAllAngularTestabilities) {
          const testabilities = win.getAllAngularTestabilities();
          let allStable = true;
          
          const whenStable = () => {
            allStable = testabilities.every(testability => testability.isStable());
            if (allStable) {
              resolve(true);
            } else {
              setTimeout(whenStable, 100);
            }
          };
          
          whenStable();
        } else {
          // No Angular detected, resolve immediately
          resolve(true);
        }
      });
    });
  });
  
  // Fill form field command
  Cypress.Commands.add('fillFormField', (fieldName: string, value: string | number | boolean) => {
    const selector = `[data-testid="form-field-${fieldName}"]`;
    
    // Get the field
    cy.get(selector).then($field => {
      const tagName = $field.prop('tagName').toLowerCase();
      const type = $field.attr('type');
      
      if (tagName === 'input') {
        if (type === 'checkbox') {
          if (value) {
            cy.get(selector).check();
          } else {
            cy.get(selector).uncheck();
          }
        } else if (type === 'radio') {
          cy.get(`${selector}[value="${value}"]`).check();
        } else if (type === 'date' || type === 'datetime-local') {
          // Handle date inputs specially
          cy.get(selector).invoke('val', value.toString()).trigger('change');
        } else {
          cy.get(selector).clear().type(value.toString());
        }
      } else if (tagName === 'select') {
        cy.get(selector).select(value.toString());
      } else if (tagName === 'textarea') {
        cy.get(selector).clear().type(value.toString());
      }
    });
  });
  
  // Check form validation
  Cypress.Commands.add('checkFormValidation', (fieldName: string, expectedState: 'valid' | 'invalid') => {
    const selector = `[data-testid="form-field-${fieldName}"]`;
    
    if (expectedState === 'valid') {
      cy.get(selector).should('not.have.class', 'ng-invalid');
      cy.get(`[data-testid="error-${fieldName}"]`).should('not.exist');
    } else {
      cy.get(selector).should('have.class', 'ng-invalid');
      cy.get(`[data-testid="error-${fieldName}"]`).should('exist');
    }
  });
  
  // Check table data
  Cypress.Commands.add('checkTableData', (expectedData: Array<Record<string, any>>) => {
    // Verify number of rows matches expected data
    cy.get('[data-testid="interaction-row"]').should('have.length', expectedData.length);
    
    // Check each row's data
    expectedData.forEach((rowData, rowIndex) => {
      Object.entries(rowData).forEach(([key, value]) => {
        cy.get(`[data-testid="interaction-row"]:nth-child(${rowIndex + 1}) [data-testid="cell-${key}"]`)
          .should('contain', value);
      });
    });
  });
}

// Initialize all commands
function initializeCommands(): void {
  registerAuthCommands();
  registerSiteCommands();
  registerInteractionCommands();
  registerUICommands();
}

// Run initialization
initializeCommands();