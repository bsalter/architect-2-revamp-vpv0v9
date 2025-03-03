import * from '../../support/e2e';

/**
 * Test suite for the Interaction Finder component which displays interactions in a
 * searchable, filterable table view with site-scoped access control.
 */
describe('Interaction Finder', () => {
  /**
   * Verifies that all required UI elements are present on the Finder page
   */
  it('displays the interaction finder page with correct elements', () => {
    // Login and set up the test environment
    cy.login('test-user', 'password');
    cy.selectSite(1);
    
    // Visit the interaction finder page
    cy.visit('/interactions');
    cy.waitForAngular();
    
    // Verify header elements
    cy.get('[data-testid="page-title"]').should('contain', 'Interactions');
    
    // Verify search elements
    cy.get('[data-testid="search-input"]').should('be.visible');
    cy.get('[data-testid="filters-button"]').should('be.visible');
    
    // Verify action buttons
    cy.get('[data-testid="create-new-button"]').should('be.visible');
    
    // Verify table exists with correct headers
    cy.get('[data-testid="interaction-table"]').should('exist');
    cy.get('[data-testid="interaction-table"] .ag-header-cell')
      .should(($cells) => {
        const headerTexts = $cells.map((i, el) => Cypress.$(el).text().trim()).get();
        expect(headerTexts).to.include.members(['Title', 'Type', 'Lead', 'Date', 'Location']);
      });
  });

  /**
   * Tests that interaction data is correctly displayed in the table
   */
  it('displays interaction data in the table', () => {
    // Login and set up the test environment
    cy.login('test-user', 'password');
    cy.selectSite(1);
    
    // Intercept and mock API response
    cy.intercept('GET', '**/api/interactions*', { 
      fixture: 'interactions/interactions.json' 
    }).as('getInteractions');
    
    // Visit the interaction finder page
    cy.visit('/interactions');
    
    // Wait for API request to complete
    cy.wait('@getInteractions');
    cy.waitForAngular();
    
    // Verify table contains the expected number of rows
    cy.get('[data-testid="interaction-row"]').should('have.length.greaterThan', 0);
    
    // Verify data in the first row
    cy.get('[data-testid="interaction-row"]:first')
      .within(() => {
        cy.get('[data-testid="cell-title"]').should('exist');
        cy.get('[data-testid="cell-type"]').should('exist');
        cy.get('[data-testid="cell-lead"]').should('exist');
        cy.get('[data-testid="cell-startDatetime"]').should('exist');
        cy.get('[data-testid="cell-location"]').should('exist');
      });
    
    // Verify pagination info displays correct total
    cy.get('[data-testid="pagination-info"]').should('exist');
  });

  /**
   * Tests the search functionality across interaction fields
   */
  it('allows searching for interactions', () => {
    // Login and set up the test environment
    cy.login('test-user', 'password');
    cy.selectSite(1);
    
    // Visit the interaction finder page
    cy.visit('/interactions');
    cy.waitForAngular();
    
    // Intercept search API calls
    cy.intercept('GET', '**/api/search/interactions*', {
      fixture: 'interactions/search-results.json'
    }).as('searchInteractions');
    
    // Type search term and submit
    const searchTerm = 'project';
    cy.get('[data-testid="search-input"]').clear().type(searchTerm);
    cy.get('[data-testid="search-input"]').type('{enter}');
    
    // Wait for search API request to complete
    cy.wait('@searchInteractions');
    cy.waitForAngular();
    
    // Verify search results are displayed
    cy.get('[data-testid="interaction-row"]').should('exist');
    
    // Verify search term is highlighted in results when available
    cy.get('[data-testid="cell-title"] .highlight-text')
      .should('exist')
      .and('contain', searchTerm);
  });

  /**
   * Tests that advanced filters correctly filter the interaction data
   */
  it('allows filtering interactions with advanced filters', () => {
    // Login and set up the test environment
    cy.login('test-user', 'password');
    cy.selectSite(1);
    
    // Visit the interaction finder page
    cy.visit('/interactions');
    cy.waitForAngular();
    
    // Intercept the filtered data API request
    cy.intercept('GET', '**/api/interactions*', {
      fixture: 'interactions/filtered-interactions.json'
    }).as('filterInteractions');
    
    // Open the filter panel
    cy.get('[data-testid="filters-button"]').click();
    
    // Verify filter panel opens
    cy.get('[data-testid="filter-panel"]').should('be.visible');
    
    // Select filter options
    // Type filter
    cy.get('[data-testid="filter-type-meeting"]').check();
    
    // Date range filter
    cy.get('[data-testid="filter-date-from"]').type('2023-06-01');
    cy.get('[data-testid="filter-date-to"]').type('2023-06-30');
    
    // Lead filter
    cy.get('[data-testid="filter-lead"]').select('J. Smith');
    
    // Apply filters
    cy.get('[data-testid="apply-filters-button"]').click();
    
    // Wait for filtered data
    cy.wait('@filterInteractions');
    cy.waitForAngular();
    
    // Verify filter indicators show active filter count
    cy.get('[data-testid="active-filters-count"]').should('contain', '3');
    
    // Verify filtered results are displayed
    cy.get('[data-testid="interaction-row"]').should('exist');
  });

  /**
   * Tests navigation to interaction details when clicking a row
   */
  it('allows navigating to interaction details', () => {
    // Login and set up the test environment
    cy.login('test-user', 'password');
    cy.selectSite(1);
    
    // Intercept interactions API
    cy.intercept('GET', '**/api/interactions*', {
      fixture: 'interactions/interactions.json'
    }).as('getInteractions');
    
    // Mock specific interaction detail API call
    cy.intercept('GET', '**/api/interactions/1', {
      body: {
        id: 1,
        title: 'Team Kickoff Meeting',
        type: 'Meeting',
        lead: 'J. Smith',
        startDatetime: '2023-06-12T10:00:00Z',
        endDatetime: '2023-06-12T11:00:00Z',
        timezone: 'America/New_York',
        location: 'Conference Room A',
        description: 'Initial project kickoff',
        notes: 'Prepare agenda beforehand'
      }
    }).as('getInteractionDetail');
    
    // Visit the interaction finder page
    cy.visit('/interactions');
    cy.wait('@getInteractions');
    cy.waitForAngular();
    
    // Click on the first row
    cy.get('[data-testid="interaction-row"]:first').click();
    
    // Wait for navigation and API call
    cy.wait('@getInteractionDetail');
    
    // Verify navigation to detail page with correct ID
    cy.url().should('include', '/interactions/1');
    cy.get('[data-testid="interaction-detail"]').should('exist');
  });

  /**
   * Tests pagination through interaction results
   */
  it('allows pagination through results', () => {
    // Login and set up the test environment
    cy.login('test-user', 'password');
    cy.selectSite(1);
    
    // Mock first page API response
    cy.intercept('GET', '**/api/interactions*', {
      fixture: 'interactions/interactions-page1.json'
    }).as('getInteractionsPage1');
    
    // Mock second page API response
    cy.intercept('GET', '**/api/interactions*page=2*', {
      fixture: 'interactions/interactions-page2.json'
    }).as('getInteractionsPage2');
    
    // Visit the interaction finder page
    cy.visit('/interactions');
    
    // Wait for first page to load
    cy.wait('@getInteractionsPage1');
    cy.waitForAngular();
    
    // Verify page 1 is active
    cy.get('[data-testid="pagination"] .active').should('contain', '1');
    
    // Save first page data for comparison
    cy.get('[data-testid="interaction-row"]:first [data-testid="cell-title"]')
      .invoke('text')
      .as('firstPageTitle');
    
    // Navigate to second page
    cy.get('[data-testid="pagination-next"]').click();
    
    // Wait for second page to load
    cy.wait('@getInteractionsPage2');
    cy.waitForAngular();
    
    // Verify page 2 is active
    cy.get('[data-testid="pagination"] .active').should('contain', '2');
    
    // Verify second page has different data than first page
    cy.get('@firstPageTitle').then(firstPageTitle => {
      cy.get('[data-testid="interaction-row"]:first [data-testid="cell-title"]')
        .invoke('text')
        .should('not.eq', firstPageTitle);
    });
  });

  /**
   * Tests that site-scoped access control works correctly
   */
  it('respects site-scoped access', () => {
    // Login as a user with access to multiple sites
    cy.login('multi-site-user', 'password');
    
    // Select first site
    cy.selectSite(1);
    
    // Intercept first site API call
    cy.intercept('GET', '**/api/interactions*', {
      fixture: 'interactions/site1-interactions.json'
    }).as('getSite1Interactions');
    
    // Visit the interactions page
    cy.visit('/interactions');
    cy.wait('@getSite1Interactions');
    cy.waitForAngular();
    
    // Verify site name is displayed
    cy.get('[data-testid="current-site"]').should('contain', 'Site 1');
    
    // Save site 1 interaction count
    cy.get('[data-testid="interaction-row"]').its('length').as('site1Count');
    
    // Save title of first interaction for comparison
    cy.get('[data-testid="interaction-row"]:first [data-testid="cell-title"]')
      .invoke('text')
      .as('site1Title');
    
    // Select second site
    cy.intercept('GET', '**/api/interactions*', {
      fixture: 'interactions/site2-interactions.json'
    }).as('getSite2Interactions');
    
    // Change site via site selector
    cy.get('[data-testid="site-selector"]').click();
    cy.get('[data-testid="site-option-2"]').click();
    
    // Wait for new data to load
    cy.wait('@getSite2Interactions');
    cy.waitForAngular();
    
    // Verify site has changed
    cy.get('[data-testid="current-site"]').should('contain', 'Site 2');
    
    // Verify different interaction data is displayed
    cy.get('@site1Title').then(site1Title => {
      cy.get('[data-testid="interaction-row"]:first [data-testid="cell-title"]')
        .invoke('text')
        .should('not.eq', site1Title);
    });
  });

  /**
   * Tests navigation to interaction creation page
   */
  it('allows creating new interactions', () => {
    // Login and set up the test environment
    cy.login('test-user', 'password');
    cy.selectSite(1);
    
    // Visit the interaction finder page
    cy.visit('/interactions');
    cy.waitForAngular();
    
    // Click the create new button
    cy.get('[data-testid="create-new-button"]').click();
    
    // Verify navigation to create page
    cy.url().should('include', '/interactions/new');
    cy.get('[data-testid="interaction-form"]').should('exist');
    cy.get('[data-testid="form-title"]').should('contain', 'Create New Interaction');
  });

  /**
   * Tests that interactions can be edited from the table
   */
  it('allows editing interactions from the table', () => {
    // Login and set up the test environment
    cy.login('test-user', 'password');
    cy.selectSite(1);
    
    // Intercept interactions API
    cy.intercept('GET', '**/api/interactions*', {
      fixture: 'interactions/interactions.json'
    }).as('getInteractions');
    
    // Visit the interaction finder page
    cy.visit('/interactions');
    cy.wait('@getInteractions');
    cy.waitForAngular();
    
    // Click edit button on first row
    cy.get('[data-testid="interaction-row"]:first [data-testid="edit-button"]').click();
    
    // Verify navigation to edit page with correct ID
    cy.url().should('include', '/interactions/');
    cy.url().should('include', '/edit');
    cy.get('[data-testid="interaction-form"]').should('exist');
    cy.get('[data-testid="form-title"]').should('contain', 'Edit Interaction');
  });

  /**
   * Tests that interactions can be deleted with confirmation dialog
   */
  it('allows deleting interactions with confirmation', () => {
    // Login and set up the test environment
    cy.login('test-user', 'password');
    cy.selectSite(1);
    
    // Intercept interactions API
    cy.intercept('GET', '**/api/interactions*', {
      fixture: 'interactions/interactions.json'
    }).as('getInteractions');
    
    // Intercept delete API
    cy.intercept('DELETE', '**/api/interactions/*', {
      statusCode: 200,
      body: { success: true }
    }).as('deleteInteraction');
    
    // Visit the interaction finder page
    cy.visit('/interactions');
    cy.wait('@getInteractions');
    cy.waitForAngular();
    
    // Store total number of rows before deletion
    cy.get('[data-testid="interaction-row"]').its('length').as('rowCountBefore');
    
    // Click delete button on first row
    cy.get('[data-testid="interaction-row"]:first [data-testid="delete-button"]').click();
    
    // Verify confirmation dialog appears
    cy.get('[data-testid="confirmation-dialog"]').should('be.visible');
    
    // Confirm deletion
    cy.get('[data-testid="confirm-delete-btn"]').click();
    
    // Wait for delete API call
    cy.wait('@deleteInteraction');
    
    // Verify success notification appears
    cy.get('[data-testid="toast-notification"]')
      .should('be.visible')
      .and('contain', 'successfully deleted');
    
    // Reload data and verify row is gone
    cy.get('@rowCountBefore').then(rowCountBefore => {
      cy.get('[data-testid="interaction-row"]').its('length').should('be.lessThan', rowCountBefore);
    });
  });

  /**
   * Tests display of empty state when no interactions exist
   */
  it('displays empty state when no interactions exist', () => {
    // Login and set up the test environment
    cy.login('test-user', 'password');
    cy.selectSite(1);
    
    // Intercept with empty response
    cy.intercept('GET', '**/api/interactions*', {
      body: {
        interactions: [],
        total: 0,
        page: 1
      }
    }).as('getEmptyInteractions');
    
    // Visit the interaction finder page
    cy.visit('/interactions');
    cy.wait('@getEmptyInteractions');
    cy.waitForAngular();
    
    // Verify empty state message is displayed
    cy.get('[data-testid="empty-state"]').should('be.visible');
    cy.get('[data-testid="empty-state-message"]')
      .should('contain', 'No interactions found');
    
    // Verify create new button is still accessible
    cy.get('[data-testid="create-new-button"]').should('be.visible');
  });

  /**
   * Tests responsive layout for mobile viewports
   */
  it('displays responsive layout on mobile viewports', () => {
    // Login and set up the test environment
    cy.login('test-user', 'password');
    cy.selectSite(1);
    
    // Intercept interactions API
    cy.intercept('GET', '**/api/interactions*', {
      fixture: 'interactions/interactions.json'
    }).as('getInteractions');
    
    // Set viewport to mobile size
    cy.viewport('iphone-x');
    
    // Visit the interaction finder page
    cy.visit('/interactions');
    cy.wait('@getInteractions');
    cy.waitForAngular();
    
    // Verify card-based layout instead of table
    cy.get('[data-testid="interaction-card"]').should('be.visible');
    cy.get('[data-testid="interaction-table"]').should('not.be.visible');
    
    // Verify all essential information is visible in card format
    cy.get('[data-testid="interaction-card"]:first').within(() => {
      cy.get('[data-testid="card-title"]').should('be.visible');
      cy.get('[data-testid="card-lead"]').should('be.visible');
      cy.get('[data-testid="card-datetime"]').should('be.visible');
      cy.get('[data-testid="card-location"]').should('be.visible');
    });
    
    // Verify action buttons are accessible
    cy.get('[data-testid="interaction-card"]:first').within(() => {
      cy.get('[data-testid="card-actions"]').should('be.visible');
      cy.get('[data-testid="card-view-button"]').should('be.visible');
      cy.get('[data-testid="card-edit-button"]').should('be.visible');
      cy.get('[data-testid="card-delete-button"]').should('be.visible');
    });
  });
});