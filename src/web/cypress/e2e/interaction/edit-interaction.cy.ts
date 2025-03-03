import * as Cypress from 'cypress'; // v12.17.3
import { interactions } from '../../fixtures/interactions/interactions.json';
import interactionDetail from '../../fixtures/interactions/interaction-detail.json';

describe('Edit Interaction', () => {
  beforeEach(() => {
    // Login using custom Cypress command
    cy.login();
    
    // Select site if needed
    cy.selectSite();
    
    // Intercept API calls for getting and updating interactions
    cy.intercept('GET', '/api/interactions/3', {
      statusCode: 200,
      body: interactionDetail
    }).as('getInteraction');
    
    cy.intercept('PUT', '/api/interactions/3', {
      statusCode: 200,
      body: {
        success: true,
        interaction: { ...interactionDetail.interaction, updatedAt: new Date().toISOString() }
      }
    }).as('updateInteraction');
    
    // Navigate to the interaction edit page
    cy.visit('/interactions/edit/3');
    
    // Wait for the API data to load
    cy.wait('@getInteraction');
  });
  
  it('should navigate to edit interaction page', () => {
    // Verify URL and page elements
    cy.url().should('include', '/interactions/edit/3');
    cy.get('h1').should('contain', 'Edit Interaction');
    cy.get('form').should('be.visible');
    cy.get('button').contains('Save').should('be.visible');
    cy.get('button').contains('Cancel').should('be.visible');
  });
  
  it('should have form pre-populated with interaction data', () => {
    // Verify all form fields are pre-populated with the correct data
    verifyFormPopulated(interactionDetail.interaction);
  });
  
  it('should update interaction successfully with valid data', () => {
    // Updated interaction data
    const updatedInteraction = {
      title: 'Updated Project Meeting',
      type: 'CALL',
      lead: 'Jane Doe',
      startDatetime: '2023-07-01T10:00:00.000Z',
      endDatetime: '2023-07-01T11:00:00.000Z',
      timezone: 'America/Chicago',
      location: 'Conference Room B',
      description: 'Updated project meeting description',
      notes: 'Updated meeting notes'
    };
    
    // Modify form fields
    modifyInteractionForm(updatedInteraction);
    
    // Submit form
    cy.get('button').contains('Save').click();
    
    // Wait for the API call and verify
    cy.wait('@updateInteraction').then((interception) => {
      expect(interception.request.body).to.include({
        title: updatedInteraction.title,
        type: updatedInteraction.type,
        lead: updatedInteraction.lead,
        location: updatedInteraction.location,
        description: updatedInteraction.description,
        notes: updatedInteraction.notes
      });
      
      // The site ID should remain unchanged to maintain site association
      expect(interception.request.body.siteId).to.equal(interactionDetail.interaction.siteId);
    });
    
    // Verify redirect to finder page
    cy.url().should('include', '/interactions');
    cy.url().should('not.include', '/edit');
    
    // Verify success message
    cy.contains('Interaction updated successfully').should('be.visible');
  });
  
  it('should show validation errors for required fields', () => {
    // Clear required fields
    cy.get('input[name="title"]').clear();
    cy.get('input[name="lead"]').clear();
    cy.get('textarea[name="description"]').clear();
    
    // Try to submit
    cy.get('button').contains('Save').click();
    
    // Verify validation errors are displayed
    verifyValidationErrors(['title', 'lead', 'description']);
    
    // Verify form was not submitted (no network request)
    cy.get('@updateInteraction.all').should('have.length', 0);
  });
  
  it('should validate date ranges', () => {
    // Set end date before start date
    const startDate = new Date(interactionDetail.interaction.startDatetime);
    const invalidEndDate = new Date(startDate);
    invalidEndDate.setHours(startDate.getHours() - 1); // Make end time before start time
    
    cy.get('input[name="endDatetime"]').clear()
      .type(invalidEndDate.toISOString().slice(0, 16)); // Format for datetime-local input
    
    // Try to submit
    cy.get('button').contains('Save').click();
    
    // Verify validation error
    cy.contains('End date must be after start date').should('be.visible');
    
    // Fix the date
    const validEndDate = new Date(startDate);
    validEndDate.setHours(startDate.getHours() + 2); // Make end time after start time
    
    cy.get('input[name="endDatetime"]').clear()
      .type(validEndDate.toISOString().slice(0, 16));
    
    // Verify error disappears
    cy.contains('End date must be after start date').should('not.exist');
  });
  
  it('should maintain site association', () => {
    // Modify title only
    cy.get('input[name="title"]').clear().type('Site Association Test');
    
    // Submit form
    cy.get('button').contains('Save').click();
    
    // Wait for the API call and verify site ID remains unchanged
    cy.wait('@updateInteraction').then((interception) => {
      expect(interception.request.body.siteId).to.equal(interactionDetail.interaction.siteId);
    });
  });
  
  it('should allow cancellation and return to finder page', () => {
    // Modify a field
    cy.get('input[name="title"]').clear().type('Cancelled Update');
    
    // Click cancel
    cy.get('button').contains('Cancel').click();
    
    // Confirm cancel in dialog
    cy.contains('Discard changes').should('be.visible');
    cy.get('button').contains('Yes, discard').click();
    
    // Verify redirect to finder without API call
    cy.url().should('include', '/interactions');
    cy.url().should('not.include', '/edit');
    cy.get('@updateInteraction.all').should('have.length', 0);
  });
  
  it('should handle API errors on submit', () => {
    // Override the intercept to return an error
    cy.intercept('PUT', '/api/interactions/3', {
      statusCode: 500,
      body: {
        error: 'Server error occurred'
      }
    }).as('updateError');
    
    // Modify a field
    cy.get('input[name="title"]').clear().type('Error Test');
    
    // Submit form
    cy.get('button').contains('Save').click();
    
    // Wait for the error response
    cy.wait('@updateError');
    
    // Verify error notification
    cy.contains('Failed to update interaction').should('be.visible');
    
    // Verify form remains on screen
    cy.url().should('include', '/interactions/edit/');
    cy.get('input[name="title"]').should('have.value', 'Error Test');
  });
});

/**
 * Helper function to modify interaction form fields
 * @param updatedInteractionData Object containing updated field values
 */
function modifyInteractionForm(updatedInteractionData: any): void {
  // Set title
  if (updatedInteractionData.title) {
    cy.get('input[name="title"]').clear().type(updatedInteractionData.title);
  }
  
  // Set type
  if (updatedInteractionData.type) {
    cy.get('select[name="type"]').select(updatedInteractionData.type);
  }
  
  // Set lead
  if (updatedInteractionData.lead) {
    cy.get('input[name="lead"]').clear().type(updatedInteractionData.lead);
  }
  
  // Set start date/time
  if (updatedInteractionData.startDatetime) {
    const formattedStart = new Date(updatedInteractionData.startDatetime)
      .toISOString().slice(0, 16); // Format for datetime-local input
    cy.get('input[name="startDatetime"]').clear().type(formattedStart);
  }
  
  // Set end date/time
  if (updatedInteractionData.endDatetime) {
    const formattedEnd = new Date(updatedInteractionData.endDatetime)
      .toISOString().slice(0, 16); // Format for datetime-local input
    cy.get('input[name="endDatetime"]').clear().type(formattedEnd);
  }
  
  // Set timezone
  if (updatedInteractionData.timezone) {
    cy.get('select[name="timezone"]').select(updatedInteractionData.timezone);
  }
  
  // Set location
  if (updatedInteractionData.location) {
    cy.get('input[name="location"]').clear().type(updatedInteractionData.location);
  }
  
  // Set description
  if (updatedInteractionData.description) {
    cy.get('textarea[name="description"]').clear().type(updatedInteractionData.description);
  }
  
  // Set notes
  if (updatedInteractionData.notes) {
    cy.get('textarea[name="notes"]').clear().type(updatedInteractionData.notes);
  }
}

/**
 * Helper function to verify form is correctly pre-populated
 * @param expectedData Expected interaction data
 */
function verifyFormPopulated(expectedData: any): void {
  // Check title
  cy.get('input[name="title"]').should('have.value', expectedData.title);
  
  // Check type
  cy.get('select[name="type"]').should('have.value', expectedData.type);
  
  // Check lead
  cy.get('input[name="lead"]').should('have.value', expectedData.lead);
  
  // Format dates for comparison with form fields
  const formattedStart = new Date(expectedData.startDatetime)
    .toISOString().slice(0, 16); // Format for datetime-local input
  const formattedEnd = new Date(expectedData.endDatetime)
    .toISOString().slice(0, 16); // Format for datetime-local input
  
  // Check start date/time
  cy.get('input[name="startDatetime"]').should('have.value', formattedStart);
  
  // Check end date/time
  cy.get('input[name="endDatetime"]').should('have.value', formattedEnd);
  
  // Check timezone
  cy.get('select[name="timezone"]').should('have.value', expectedData.timezone);
  
  // Check location
  cy.get('input[name="location"]').should('have.value', expectedData.location);
  
  // Check description
  cy.get('textarea[name="description"]').should('have.value', expectedData.description);
  
  // Check notes
  cy.get('textarea[name="notes"]').should('have.value', expectedData.notes);
}

/**
 * Helper function to verify form validation errors
 * @param fieldNames Array of field names to check for errors
 */
function verifyValidationErrors(fieldNames: string[]): void {
  // Check for error messages on each field
  fieldNames.forEach(fieldName => {
    cy.get(`[name="${fieldName}"]`)
      .parents('.form-group')
      .find('.error-message')
      .should('be.visible');
  });
  
  // Verify save button is disabled
  cy.get('button').contains('Save').should('be.disabled');
}