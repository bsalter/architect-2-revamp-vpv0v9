/// <reference types="cypress" />

import '../../support/e2e';

describe('Interaction Search', () => {
  beforeEach(() => {
    // Login as a standard user
    cy.login('testuser', 'TestPassword123!');
    
    // Select a site
    cy.selectSite(1);
  });

  it('should load the interaction finder page with search elements', () => {
    cy.visit('/interactions');
    cy.waitForAngular();
    
    // Verify search elements are present
    cy.get('[data-cy=search-input]').should('be.visible');
    cy.get('[data-cy=filter-button]').should('be.visible');
    cy.get('[data-cy=filter-button]').should('contain', '0'); // Initially no filters
  });

  it('should perform a basic search with global search term', () => {
    // Intercept search API call and mock response
    cy.intercept('GET', '/api/search/interactions*', {
      fixture: 'interactions/search-results.json'
    }).as('searchInteractions');
    
    cy.visit('/interactions');
    cy.waitForAngular();
    
    // Type search term in search input
    cy.get('[data-cy=search-input]').type('project');
    cy.get('[data-cy=search-input]').type('{enter}');
    
    // Wait for search API call to complete
    cy.wait('@searchInteractions');
    cy.waitForAngular();
    
    // Verify that search results are displayed
    cy.get('[data-cy=finder-table]').should('be.visible');
    
    // Verify that the correct number of results is shown
    cy.get('[data-cy=results-count]').should('be.visible');
    
    // Verify that search term is highlighted in results
    cy.get('em').should('contain', 'project');
  });

  it('should use the advanced filter panel', () => {
    // Intercept filter API call
    cy.intercept('GET', '/api/search/interactions*', {
      fixture: 'interactions/search-results.json'
    }).as('filterInteractions');
    
    cy.visit('/interactions');
    cy.waitForAngular();
    
    // Open filter panel
    cy.get('[data-cy=filter-button]').click();
    
    // Verify filter panel is visible
    cy.get('[data-cy=filter-panel]').should('be.visible');
    
    // Select 'Meeting' as type filter
    cy.get('[data-cy=filter-type]').select('Meeting');
    
    // Select date range filters
    cy.get('[data-cy=date-range-filter]').within(() => {
      cy.get('[data-cy=start-date]').type('2023-06-01');
      cy.get('[data-cy=end-date]').type('2023-06-30');
    });
    
    // Click 'Apply' button
    cy.get('[data-cy=apply-filters]').click();
    
    // Wait for filter API call to complete
    cy.wait('@filterInteractions');
    cy.waitForAngular();
    
    // Verify that filtered results are displayed
    cy.get('[data-cy=finder-table]').should('be.visible');
    
    // Verify filter button shows count of active filters
    cy.get('[data-cy=filter-button]').should('contain', '2');
  });

  it('should combine global search with advanced filters', () => {
    // Intercept combined search API call
    cy.intercept('GET', '/api/search/interactions*globalSearch=project*type=Meeting*', {
      fixture: 'interactions/search-results.json'
    }).as('combinedSearch');
    
    cy.visit('/interactions');
    cy.waitForAngular();
    
    // Type search term
    cy.get('[data-cy=search-input]').type('project');
    
    // Open filter panel
    cy.get('[data-cy=filter-button]').click();
    
    // Select 'Meeting' as type filter
    cy.get('[data-cy=filter-type]').select('Meeting');
    
    // Click 'Apply' button
    cy.get('[data-cy=apply-filters]').click();
    
    // Wait for combined search API call to complete
    cy.wait('@combinedSearch');
    cy.waitForAngular();
    
    // Verify that search results include both global term and filters
    cy.get('[data-cy=finder-table]').should('be.visible');
    
    // Verify that the correct result count is displayed
    cy.get('[data-cy=results-count]').should('be.visible');
  });

  it('should clear search results', () => {
    // Intercept initial search
    cy.intercept('GET', '/api/search/interactions*', {
      fixture: 'interactions/search-results.json'
    }).as('searchInteractions');
    
    // Intercept clear search (which returns all interactions)
    cy.intercept('GET', '/api/interactions*', {
      fixture: 'interactions/interactions.json'
    }).as('getInteractions');
    
    cy.visit('/interactions');
    cy.waitForAngular();
    
    // Type search term in search input
    cy.get('[data-cy=search-input]').type('project');
    cy.get('[data-cy=search-input]').type('{enter}');
    
    // Wait for search results to load
    cy.wait('@searchInteractions');
    cy.waitForAngular();
    
    // Clear the search input
    cy.get('[data-cy=search-input]').clear().type('{enter}');
    
    cy.wait('@getInteractions');
    cy.waitForAngular();
    
    // Verify that all interactions are displayed without filtering
    cy.get('[data-cy=finder-table]').should('be.visible');
    
    // Verify that filter count returns to 0
    cy.get('[data-cy=filter-button]').should('contain', '0');
  });

  it('should clear filters', () => {
    // Intercept filter API calls
    cy.intercept('GET', '/api/search/interactions*', {
      fixture: 'interactions/search-results.json'
    }).as('filterInteractions');
    
    cy.intercept('GET', '/api/interactions*', {
      fixture: 'interactions/interactions.json'
    }).as('getInteractions');
    
    cy.visit('/interactions');
    cy.waitForAngular();
    
    // Open the filter panel
    cy.get('[data-cy=filter-button]').click();
    
    // Apply multiple filters
    cy.get('[data-cy=filter-type]').select('Meeting');
    cy.get('[data-cy=date-range-filter]').within(() => {
      cy.get('[data-cy=start-date]').type('2023-06-01');
      cy.get('[data-cy=end-date]').type('2023-06-30');
    });
    
    // Apply filters
    cy.get('[data-cy=apply-filters]').click();
    
    cy.wait('@filterInteractions');
    cy.waitForAngular();
    
    // Verify filter count shows correct number
    cy.get('[data-cy=filter-button]').should('contain', '2');
    
    // Open filter panel again
    cy.get('[data-cy=filter-button]').click();
    
    // Click 'Clear Filters' button in filter panel
    cy.get('[data-cy=clear-filters]').click();
    
    cy.wait('@getInteractions');
    cy.waitForAngular();
    
    // Verify that filter count returns to 0
    cy.get('[data-cy=filter-button]').should('contain', '0');
    
    // Verify that all interactions are displayed without filtering
    cy.get('[data-cy=finder-table]').should('be.visible');
  });

  it('should show empty state for no search results', () => {
    // Intercept search API call and mock empty results response
    cy.intercept('GET', '/api/search/interactions?globalSearch=noresults*', {
      body: {
        interactions: [],
        total: 0,
        page: 1,
        pageSize: 10,
        executionTimeMs: 50
      }
    }).as('emptySearch');
    
    cy.visit('/interactions');
    cy.waitForAngular();
    
    // Type search term that will return no results
    cy.get('[data-cy=search-input]').type('noresults');
    cy.get('[data-cy=search-input]').type('{enter}');
    
    // Wait for search API call to complete
    cy.wait('@emptySearch');
    cy.waitForAngular();
    
    // Verify that empty state message is displayed
    cy.get('[data-cy=empty-state]').should('be.visible');
    cy.get('[data-cy=empty-state]').should('contain', 'No results found');
    
    // Verify that table does not show any rows
    cy.get('[data-cy=finder-table] tbody tr').should('not.exist');
  });

  it('should respect site-scoped access in search results', () => {
    // Login as a user with access to multiple sites
    cy.login('multisite-user', 'TestPassword123!');
    
    // Select first site
    cy.selectSite(1);
    
    // Intercept search API call and mock response with site-specific results
    cy.intercept('GET', '/api/search/interactions*', {
      body: {
        interactions: [
          {
            id: 1,
            title: 'Site 1 Project Meeting',
            type: 'Meeting',
            lead: 'J. Smith',
            startDatetime: '2023-06-15T10:00:00Z',
            endDatetime: '2023-06-15T11:00:00Z',
            location: 'HQ Conference Room',
            siteId: 1
          }
        ],
        total: 1,
        page: 1,
        pageSize: 10
      }
    }).as('site1Search');
    
    cy.visit('/interactions');
    cy.waitForAngular();
    
    // Perform search with term 'project'
    cy.get('[data-cy=search-input]').type('project');
    cy.get('[data-cy=search-input]').type('{enter}');
    
    cy.wait('@site1Search');
    cy.waitForAngular();
    
    // Verify results belong to selected site
    cy.get('[data-cy=finder-table]').contains('Site 1 Project Meeting').should('be.visible');
    
    // Select second site
    cy.selectSite(2);
    
    // Intercept search API call for second site and mock different response
    cy.intercept('GET', '/api/search/interactions*', {
      body: {
        interactions: [
          {
            id: 2,
            title: 'Site 2 Project Update',
            type: 'Meeting',
            lead: 'M. Johnson',
            startDatetime: '2023-06-16T14:00:00Z',
            endDatetime: '2023-06-16T15:00:00Z',
            location: 'Branch Office',
            siteId: 2
          }
        ],
        total: 1,
        page: 1,
        pageSize: 10
      }
    }).as('site2Search');
    
    cy.visit('/interactions');
    cy.waitForAngular();
    
    // Perform same search with term 'project'
    cy.get('[data-cy=search-input]').type('project');
    cy.get('[data-cy=search-input]').type('{enter}');
    
    cy.wait('@site2Search');
    cy.waitForAngular();
    
    // Verify results now belong to second site only
    cy.get('[data-cy=finder-table]').contains('Site 2 Project Update').should('be.visible');
    cy.get('[data-cy=finder-table]').contains('Site 1 Project Meeting').should('not.exist');
  });

  it('should paginate through search results', () => {
    // Intercept search API call for page 1 and mock response with paginated results
    cy.intercept('GET', '/api/search/interactions*page=1*', {
      body: {
        interactions: [
          {
            id: 1,
            title: 'Project Meeting 1',
            type: 'Meeting',
            lead: 'J. Smith',
            startDatetime: '2023-06-15T10:00:00Z',
            endDatetime: '2023-06-15T11:00:00Z',
            location: 'Room A'
          },
          {
            id: 2,
            title: 'Project Meeting 2',
            type: 'Meeting',
            lead: 'J. Smith',
            startDatetime: '2023-06-16T10:00:00Z',
            endDatetime: '2023-06-16T11:00:00Z',
            location: 'Room B'
          }
        ],
        total: 12, // Total of 12 results across pages
        page: 1,
        pageSize: 2, // 2 items per page for testing
        totalPages: 6
      }
    }).as('page1Search');
    
    cy.visit('/interactions');
    cy.waitForAngular();
    
    // Perform search that returns multiple pages of results
    cy.get('[data-cy=search-input]').type('project');
    cy.get('[data-cy=search-input]').type('{enter}');
    
    cy.wait('@page1Search');
    cy.waitForAngular();
    
    // Verify page 1 is active
    cy.get('[data-cy=pagination]').should('contain', '1');
    cy.get('[data-cy=pagination] .active').should('contain', '1');
    
    // Verify correct results for page 1 are displayed
    cy.get('[data-cy=finder-table]').contains('Project Meeting 1').should('be.visible');
    cy.get('[data-cy=finder-table]').contains('Project Meeting 2').should('be.visible');
    
    // Intercept search API call for page 2 and mock response with page 2 results
    cy.intercept('GET', '/api/search/interactions*page=2*', {
      body: {
        interactions: [
          {
            id: 3,
            title: 'Project Meeting 3',
            type: 'Meeting',
            lead: 'M. Jones',
            startDatetime: '2023-06-17T10:00:00Z',
            endDatetime: '2023-06-17T11:00:00Z',
            location: 'Room C'
          },
          {
            id: 4,
            title: 'Project Meeting 4',
            type: 'Meeting',
            lead: 'M. Jones',
            startDatetime: '2023-06-18T10:00:00Z',
            endDatetime: '2023-06-18T11:00:00Z',
            location: 'Room D'
          }
        ],
        total: 12,
        page: 2,
        pageSize: 2,
        totalPages: 6
      }
    }).as('page2Search');
    
    // Click on next page button
    cy.get('[data-cy=pagination]').contains('2').click();
    
    // Wait for page 2 API call to complete
    cy.wait('@page2Search');
    cy.waitForAngular();
    
    // Verify page 2 is active
    cy.get('[data-cy=pagination] .active').should('contain', '2');
    
    // Verify correct results for page 2 are displayed
    cy.get('[data-cy=finder-table]').contains('Project Meeting 3').should('be.visible');
    cy.get('[data-cy=finder-table]').contains('Project Meeting 4').should('be.visible');
  });

  it('should persist search term in URL', () => {
    // Intercept search API calls
    cy.intercept('GET', '/api/search/interactions*globalSearch=project*', {
      fixture: 'interactions/search-results.json'
    }).as('searchInteractions');
    
    cy.visit('/interactions');
    cy.waitForAngular();
    
    // Type search term in search input
    cy.get('[data-cy=search-input]').type('project');
    cy.get('[data-cy=search-input]').type('{enter}');
    
    // Wait for search results to load
    cy.wait('@searchInteractions');
    cy.waitForAngular();
    
    // Verify that URL contains search term parameter
    cy.url().should('include', 'search=project');
    
    // Reload the page
    cy.reload();
    
    // Wait for API call (should be made again with search term from URL)
    cy.wait('@searchInteractions');
    cy.waitForAngular();
    
    // Verify that search term is preserved in input
    cy.get('[data-cy=search-input]').should('have.value', 'project');
    
    // Verify that same search results are displayed
    cy.get('[data-cy=finder-table]').should('be.visible');
  });
});