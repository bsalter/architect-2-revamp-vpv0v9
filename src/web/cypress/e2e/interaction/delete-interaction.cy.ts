import { username, password, sites } from '../../fixtures/auth/user.json';
import interactions from '../../fixtures/interactions/interactions.json';

describe('Interaction Deletion', () => {
  beforeEach(() => {
    // Login to the application using custom login command
    cy.login(username, password);
    
    // Select a site if multiple sites are available
    if (sites && sites.length > 1) {
      cy.selectSite(sites[0].name);
    }
    
    // Set up API route interception for interactions
    cy.intercept('GET', '/api/interactions*', { fixture: 'interactions/interactions.json' }).as('getInteractions');
    cy.intercept('DELETE', '/api/interactions/*').as('deleteInteraction');
    cy.intercept('GET', '/api/interactions/*').as('getInteractionDetail');
    
    // Navigate to the interaction finder page
    cy.visit('/interactions');
    
    // Wait for interaction data to load in the finder
    cy.wait('@getInteractions');
  });

  it('should successfully delete an interaction with confirmation', () => {
    // Get initial count of interactions
    const initialCount = interactions.interactions.length;
    
    // Select an interaction to delete from the finder
    cy.get('.ag-row').first().click();
    
    // Click the delete button
    cy.get('[data-cy=delete-button]').click();
    
    // Verify the confirmation modal appears with correct interaction details
    cy.get('[data-cy=delete-confirmation-modal]').should('be.visible');
    cy.get('[data-cy=modal-title]').should('contain', 'Confirm Deletion');
    
    const interactionToDelete = interactions.interactions[0];
    cy.get('[data-cy=delete-confirmation-modal]').should('contain', interactionToDelete.title);
    cy.get('[data-cy=delete-confirmation-modal]').should('contain', 
      new Date(interactionToDelete.startDatetime).toLocaleString());
    
    // Confirm the deletion in the modal
    cy.get('[data-cy=confirm-delete]').click();
    
    // Verify the DELETE API request is made with correct ID
    cy.wait('@deleteInteraction')
      .its('request.url')
      .should('include', `/api/interactions/${interactionToDelete.id}`);
    
    // Verify successful completion notification is shown
    cy.get('[data-cy=toast-success]').should('be.visible');
    cy.get('[data-cy=toast-success]').should('contain', 'deleted successfully');
    
    // Verify the deleted interaction is no longer in the finder table
    cy.get('.ag-row').should('have.length', initialCount - 1);
    cy.get(".ag-cell[col-id='title']").should('not.contain', interactionToDelete.title);
  });

  it('should cancel the interaction deletion process', () => {
    // Select an interaction to delete from the finder
    cy.get('.ag-row').first().click();
    
    // Click the delete button
    cy.get('[data-cy=delete-button]').click();
    
    // Verify the confirmation modal appears
    cy.get('[data-cy=delete-confirmation-modal]').should('be.visible');
    
    // Click the cancel button on the confirmation modal
    cy.get('[data-cy=cancel-delete]').click();
    
    // Verify the modal closes
    cy.get('[data-cy=delete-confirmation-modal]').should('not.exist');
    
    // Verify no DELETE API request was made
    cy.get('@deleteInteraction.all').should('have.length', 0);
    
    // Verify the interaction still exists in the finder table
    const interactionTitle = interactions.interactions[0].title;
    cy.get(".ag-cell[col-id='title']").should('contain', interactionTitle);
  });

  it('should delete an interaction from the detail view', () => {
    // Navigate directly to an interaction detail view
    const interaction = interactions.interactions[0];
    cy.visit(`/interactions/${interaction.id}`);
    cy.wait('@getInteractionDetail');
    
    // Verify we're on the detail view
    cy.get('[data-cy=interaction-title]').should('contain', interaction.title);
    
    // Click the delete button in the detail view
    cy.get('[data-cy=delete-button]').click();
    
    // Verify the confirmation modal appears
    cy.get('[data-cy=delete-confirmation-modal]').should('be.visible');
    
    // Confirm the deletion
    cy.get('[data-cy=confirm-delete]').click();
    
    // Verify the DELETE API request is made
    cy.wait('@deleteInteraction');
    
    // Verify redirection to the finder page after successful deletion
    cy.url().should('include', '/interactions');
    cy.url().should('not.include', `/${interaction.id}`);
    
    // Wait for the finder to load after redirection
    cy.wait('@getInteractions');
    
    // Verify the interaction is no longer in the finder table
    cy.get(".ag-cell[col-id='title']").should('not.contain', interaction.title);
  });

  it('should handle error during deletion', () => {
    // Intercept DELETE request and mock a server error response
    cy.intercept('DELETE', '/api/interactions/*', {
      statusCode: 500,
      body: { message: 'Internal server error' }
    }).as('deleteError');
    
    // Select an interaction to delete
    cy.get('.ag-row').first().click();
    
    // Click the delete button
    cy.get('[data-cy=delete-button]').click();
    
    // Confirm the deletion in the modal
    cy.get('[data-cy=confirm-delete]').click();
    
    // Verify error notification is displayed to the user
    cy.get('[data-cy=error-message]').should('be.visible');
    cy.get('[data-cy=error-message]').should('contain', 'Failed to delete interaction');
    
    // Verify the modal remains open with error state
    cy.get('[data-cy=delete-confirmation-modal]').should('be.visible');
    
    // Verify the interaction still exists in the finder after error
    const interactionTitle = interactions.interactions[0].title;
    cy.get(".ag-cell[col-id='title']").should('contain', interactionTitle);
  });

  it('should not allow unauthorized deletion', () => {
    // Intercept DELETE request and mock a 403 Forbidden response
    cy.intercept('DELETE', '/api/interactions/*', {
      statusCode: 403,
      body: { message: 'You do not have permission to delete this interaction' }
    }).as('deleteUnauthorized');
    
    // Attempt to delete an interaction
    cy.get('.ag-row').first().click();
    cy.get('[data-cy=delete-button]').click();
    
    // Confirm the deletion in the modal
    cy.get('[data-cy=confirm-delete]').click();
    
    // Verify error notification indicates access denied
    cy.get('[data-cy=error-message]').should('be.visible');
    cy.get('[data-cy=error-message]').should('contain', 'permission');
    
    // Verify the modal closes and shows appropriate error message
    cy.get('[data-cy=delete-confirmation-modal]').should('not.exist');
    
    // Verify the interaction remains in the finder
    const interactionTitle = interactions.interactions[0].title;
    cy.get(".ag-cell[col-id='title']").should('contain', interactionTitle);
  });

  it('should verify that batch deletion is not supported', () => {
    // Attempt to select multiple interactions in the finder
    cy.get('.ag-row').first().click();
    cy.get('body').type('{ctrl}', { release: false });
    cy.get('.ag-row').eq(1).click();
    cy.get('body').type('{ctrl}', { release: true });
    
    // Verify that multiple selection is not supported (only one row can be selected)
    cy.get('.ag-row-selected').should('have.length', 1);
    
    // Deselect all rows
    cy.get('body').click({ force: true });
    
    // Verify that delete button is disabled when no single row is selected
    cy.get('[data-cy=delete-button]').should('be.disabled');
    
    // Can also use the custom delete interaction command to verify it works only with a selected row
    cy.get('.ag-row').should('exist');
    cy.get('[data-cy=delete-button]').should('be.disabled');
    cy.deleteInteraction().should('not.exist');
  });
});