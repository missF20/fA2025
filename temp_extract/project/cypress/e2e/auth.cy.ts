describe('Authentication', () => {
  beforeEach(() => {
    cy.visit('/');
  });

  it('should allow users to sign in', () => {
    cy.get('input[type="email"]').type('test@example.com');
    cy.get('input[type="password"]').type('Password123');
    cy.get('button[type="submit"]').click();
    cy.url().should('include', '/dashboard');
  });

  it('should show error message for invalid credentials', () => {
    cy.get('input[type="email"]').type('invalid@example.com');
    cy.get('input[type="password"]').type('wrongpassword');
    cy.get('button[type="submit"]').click();
    cy.contains('Invalid login credentials').should('be.visible');
  });

  it('should persist session after refresh', () => {
    cy.login('test@example.com', 'Password123');
    cy.reload();
    cy.url().should('include', '/dashboard');
  });
});