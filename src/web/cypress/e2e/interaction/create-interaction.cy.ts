// Cypress version: 12.17.3
import { interactionDetail } from '../../fixtures/interactions/interaction-detail.json';

describe('Interaction Creation', () => {
  beforeEach(() => {
    // Login and navigate to the interaction creation page
    cy.login();
    cy.selectSite();
    cy.visit('/interactions');
    
    // Intercept the create interaction API requests
    cy.intercept('POST', '/api/interactions').as('createInteraction');
    
    // Click on New Interaction button
    cy.get('[data-testid="create-interaction-btn"]').click();
    
    // Wait for the form to load
    cy.url().should('include', '/interactions/create');
    cy.get('[data-testid="interaction-form"]').should('be.visible');
  });

  it('should navigate to create interaction page', () => {
    // Verify URL and page title
    cy.url().should('include', '/interactions/create');
    cy.get('[data-testid="page-title"]').should('contain', 'Create New Interaction');
    
    // Verify all form fields are present
    cy.get('[data-testid="title-input"]').should('be.visible');
    cy.get('[data-testid="type-select"]').should('be.visible');
    cy.get('[data-testid="lead-input"]').should('be.visible');
    cy.get('[data-testid="start-datetime-input"]').should('be.visible');
    cy.get('[data-testid="end-datetime-input"]').should('be.visible');
    cy.get('[data-testid="timezone-select"]').should('be.visible');
    cy.get('[data-testid="location-input"]').should('be.visible');
    cy.get('[data-testid="description-textarea"]').should('be.visible');
    cy.get('[data-testid="notes-textarea"]').should('be.visible');
    
    // Verify action buttons
    cy.get('[data-testid="save-btn"]').should('be.visible');
    cy.get('[data-testid="cancel-btn"]').should('be.visible');
  });

  it('should create interaction successfully with valid data', () => {
    // Fill form with valid data
    fillInteractionForm({
      title: interactionDetail.title,
      type: interactionDetail.type,
      lead: interactionDetail.lead,
      startDatetime: interactionDetail.startDatetime,
      endDatetime: interactionDetail.endDatetime,
      timezone: interactionDetail.timezone,
      location: interactionDetail.location,
      description: interactionDetail.description,
      notes: interactionDetail.notes
    });
    
    // Submit the form
    cy.get('[data-testid="save-btn"]').click();
    
    // Verify API call
    cy.wait('@createInteraction').then((interception) => {
      // Verify request payload
      expect(interception.request.body).to.have.property('title', interactionDetail.title);
      expect(interception.request.body).to.have.property('type', interactionDetail.type);
      expect(interception.request.body).to.have.property('lead', interactionDetail.lead);
      expect(interception.request.body).to.have.property('description', interactionDetail.description);
      
      // Verify that the interaction is associated with the current site
      cy.getSiteContext().then((siteContext) => {
        expect(interception.request.body).to.have.property('siteId', siteContext.siteId);
      });
    });
    
    // Verify redirect to finder page
    cy.url().should('include', '/interactions');
    
    // Verify success notification
    cy.get('[data-testid="success-notification"]').should('be.visible');
    cy.get('[data-testid="success-notification"]').should('contain', 'Interaction created successfully');
  });

  it('should show validation errors for required fields', () => {
    // Try to submit form without filling any fields
    cy.get('[data-testid="save-btn"]').click();
    
    // Verify validation errors for required fields
    verifyValidationErrors(['title', 'type', 'lead', 'start-datetime', 'end-datetime', 'timezone', 'description']);
    
    // Form submission should be prevented
    cy.get('@createInteraction.all').should('have.length', 0);
  });

  it('should validate date ranges', () => {
    // Fill other required fields
    fillInteractionForm({
      title: interactionDetail.title,
      type: interactionDetail.type,
      lead: interactionDetail.lead,
      // Do not fill dates yet
      timezone: interactionDetail.timezone,
      location: interactionDetail.location,
      description: interactionDetail.description,
      notes: interactionDetail.notes
    });
    
    // Set end date before start date
    const startDate = new Date('2023-06-20T10:00:00.000Z');
    const endDate = new Date('2023-06-20T09:00:00.000Z'); // 1 hour before start
    
    cy.get('[data-testid="start-datetime-input"]').type(startDate.toISOString().slice(0, 16).replace('T', ' '));
    cy.get('[data-testid="end-datetime-input"]').type(endDate.toISOString().slice(0, 16).replace('T', ' '));
    
    // Try to submit form
    cy.get('[data-testid="save-btn"]').click();
    
    // Verify date validation error
    cy.get('[data-testid="end-datetime-error"]').should('be.visible');
    cy.get('[data-testid="end-datetime-error"]').should('contain', 'End date must be after start date');
    
    // Fix date range and verify error disappears
    const correctedEndDate = new Date('2023-06-20T11:00:00.000Z'); // 1 hour after start
    cy.get('[data-testid="end-datetime-input"]').clear().type(correctedEndDate.toISOString().slice(0, 16).replace('T', ' '));
    cy.get('[data-testid="end-datetime-error"]').should('not.exist');
  });

  it('should associate interaction with current site', () => {
    // Fill form with valid data
    fillInteractionForm({
      title: interactionDetail.title,
      type: interactionDetail.type,
      lead: interactionDetail.lead,
      startDatetime: interactionDetail.startDatetime,
      endDatetime: interactionDetail.endDatetime,
      timezone: interactionDetail.timezone,
      location: interactionDetail.location,
      description: interactionDetail.description,
      notes: interactionDetail.notes
    });
    
    // Submit the form
    cy.get('[data-testid="save-btn"]').click();
    
    // Verify site association in API call
    cy.wait('@createInteraction').then((interception) => {
      cy.getSiteContext().then((siteContext) => {
        expect(interception.request.body).to.have.property('siteId', siteContext.siteId);
      });
    });
  });

  it('should allow cancellation and return to finder page', () => {
    // Fill some form fields
    cy.get('[data-testid="title-input"]').type('Draft Interaction');
    cy.get('[data-testid="description-textarea"]').type('Some draft description');
    
    // Click cancel button
    cy.get('[data-testid="cancel-btn"]').click();
    
    // Confirm cancellation in dialog
    cy.get('[data-testid="confirm-dialog"]').should('be.visible');
    cy.get('[data-testid="confirm-yes-btn"]').click();
    
    // Verify navigation to finder page
    cy.url().should('include', '/interactions');
    cy.url().should('not.include', '/create');
    
    // Verify no API calls were made
    cy.get('@createInteraction.all').should('have.length', 0);
  });

  it('should handle API errors on submit', () => {
    // Stub API to return an error
    cy.intercept('POST', '/api/interactions', {
      statusCode: 500,
      body: {
        error: 'Internal Server Error',
        message: 'Failed to create interaction'
      }
    }).as('createInteractionError');
    
    // Fill form with valid data
    fillInteractionForm({
      title: interactionDetail.title,
      type: interactionDetail.type,
      lead: interactionDetail.lead,
      startDatetime: interactionDetail.startDatetime,
      endDatetime: interactionDetail.endDatetime,
      timezone: interactionDetail.timezone,
      location: interactionDetail.location,
      description: interactionDetail.description,
      notes: interactionDetail.notes
    });
    
    // Submit the form
    cy.get('[data-testid="save-btn"]').click();
    
    // Wait for error response
    cy.wait('@createInteractionError');
    
    // Verify error notification
    cy.get('[data-testid="error-notification"]').should('be.visible');
    cy.get('[data-testid="error-notification"]').should('contain', 'Failed to create interaction');
    
    // Verify form still displayed with entered data
    cy.url().should('include', '/interactions/create');
    cy.get('[data-testid="title-input"]').should('have.value', interactionDetail.title);
    cy.get('[data-testid="description-textarea"]').should('have.value', interactionDetail.description);
  });

  /**
   * Helper function to fill interaction form fields
   */
  function fillInteractionForm(interactionData: {
    title?: string;
    type?: string;
    lead?: string;
    startDatetime?: string;
    endDatetime?: string;
    timezone?: string;
    location?: string;
    description?: string;
    notes?: string;
  }) {
    // Fill title if provided
    if (interactionData.title) {
      cy.get('[data-testid="title-input"]').type(interactionData.title);
    }
    
    // Select type if provided
    if (interactionData.type) {
      cy.get('[data-testid="type-select"]').click();
      cy.get(`[data-value="${interactionData.type}"]`).click();
    }
    
    // Fill lead if provided
    if (interactionData.lead) {
      cy.get('[data-testid="lead-input"]').type(interactionData.lead);
    }
    
    // Set start datetime if provided
    if (interactionData.startDatetime) {
      const startDate = new Date(interactionData.startDatetime);
      cy.get('[data-testid="start-datetime-input"]').type(
        startDate.toISOString().slice(0, 16).replace('T', ' ')
      );
    }
    
    // Set end datetime if provided
    if (interactionData.endDatetime) {
      const endDate = new Date(interactionData.endDatetime);
      cy.get('[data-testid="end-datetime-input"]').type(
        endDate.toISOString().slice(0, 16).replace('T', ' ')
      );
    }
    
    // Select timezone if provided
    if (interactionData.timezone) {
      cy.get('[data-testid="timezone-select"]').click();
      cy.get(`[data-value="${interactionData.timezone}"]`).click();
    }
    
    // Fill location if provided (optional field)
    if (interactionData.location) {
      cy.get('[data-testid="location-input"]').type(interactionData.location);
    }
    
    // Fill description if provided
    if (interactionData.description) {
      cy.get('[data-testid="description-textarea"]').type(interactionData.description);
    }
    
    // Fill notes if provided (optional field)
    if (interactionData.notes) {
      cy.get('[data-testid="notes-textarea"]').type(interactionData.notes);
    }
  }

  /**
   * Helper function to verify validation errors for specified fields
   */
  function verifyValidationErrors(fieldNames: string[]) {
    fieldNames.forEach(fieldName => {
      cy.get(`[data-testid="${fieldName}-error"]`).should('be.visible');
      
      // Verify appropriate error message based on field type
      switch (fieldName) {
        case 'title':
          cy.get(`[data-testid="${fieldName}-error"]`).should('contain', 'Title is required');
          break;
        case 'type':
          cy.get(`[data-testid="${fieldName}-error"]`).should('contain', 'Type is required');
          break;
        case 'lead':
          cy.get(`[data-testid="${fieldName}-error"]`).should('contain', 'Lead is required');
          break;
        case 'start-datetime':
          cy.get(`[data-testid="${fieldName}-error"]`).should('contain', 'Start date/time is required');
          break;
        case 'end-datetime':
          cy.get(`[data-testid="${fieldName}-error"]`).should('contain', 'End date/time is required');
          break;
        case 'timezone':
          cy.get(`[data-testid="${fieldName}-error"]`).should('contain', 'Timezone is required');
          break;
        case 'description':
          cy.get(`[data-testid="${fieldName}-error"]`).should('contain', 'Description is required');
          break;
        default:
          cy.get(`[data-testid="${fieldName}-error"]`).should('be.visible');
      }
    });
    
    // Verify save button is disabled
    cy.get('[data-testid="save-btn"]').should('be.disabled');
  }
});