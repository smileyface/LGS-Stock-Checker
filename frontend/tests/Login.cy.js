import { mount } from '@cypress/vue'
import Login from './Login.vue'
import { authStore } from '../stores/auth'

// Mock the router used by the authStore to prevent errors during testing
vi.mock('../router', () => ({
  default: {
    push: vi.fn(),
  },
}));

describe('<Login />', () => {
  // Reset mocks before each test
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the login form correctly', () => {
    mount(Login)

    // Assert that the form elements exist
    cy.get('h2').should('contain', 'LGS Stock Checker')
    cy.get('input#username').should('be.visible')
    cy.get('input#password').should('be.visible')
    cy.get('button[type="submit"]').should('contain', 'Login')
  })

  it('allows the user to type into the input fields', () => {
    mount(Login)

    cy.get('input#username').type('testuser')
    cy.get('input#password').type('password123')

    cy.get('input#username').should('have.value', 'testuser')
    cy.get('input#password').should('have.value', 'password123')
  })

  it('calls the auth store on form submission', () => {
    // Spy on the authStore's login method
    const loginSpy = cy.spy(authStore, 'login').as('loginSpy')

    mount(Login)

    cy.get('input#username').type('testuser')
    cy.get('input#password').type('password123')
    cy.get('form').submit()

    // Assert that the spy was called with the correct credentials
    cy.get('@loginSpy').should('have.been.calledWith', {
      username: 'testuser',
      password: 'password123'
    })
  })
})
