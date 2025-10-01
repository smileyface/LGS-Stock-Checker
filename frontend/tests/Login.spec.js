import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { mount } from '@vue/test-utils';
import axios from 'axios';
import Login from '../src/views/Login.vue'
import { authStore } from '../src/stores/auth'
import router from '../src/router'

// Mock the axios library to prevent actual network calls
vi.mock('axios', () => ({
    default: {
        post: vi.fn(() => Promise.resolve({ data: {} })),
        get: vi.fn(() => Promise.resolve({ data: {} })), // Also mock get for checkAuthStatus
    }
}));

// Mock the router used by the authStore to prevent errors during testing
// The path here must match the import path inside `auth.js` relative to `auth.js` itself.
vi.mock('../src/router', () => ({
    default: {
        push: vi.fn(),
        replace: vi.fn(),
    },
}));

describe('Login.vue', () => {
    // Reset mocks before each test
    beforeEach(() => {
        vi.clearAllMocks();
    });

    // Restore all spies and mocks to their original state after each test
    afterEach(() => {
        vi.restoreAllMocks();
    });

    it('renders the login form correctly', () => {
        const wrapper = mount(Login, {
            global: {
                stubs: {
                    RouterLink: true // Stub RouterLink to prevent warnings
                }
            }
        })

        // Assert that the form elements exist
        expect(wrapper.find('h2').text()).toContain('LGS Stock Checker')
        expect(wrapper.find('input#username').exists()).toBe(true)
        expect(wrapper.find('input#password').exists()).toBe(true)
        expect(wrapper.find('button[type="submit"]').text()).toContain('Login')
    })

    it('allows the user to type into the input fields', async () => {
        const wrapper = mount(Login, {
            global: {
                stubs: {
                    RouterLink: true
                }
            }
        })

        await wrapper.find('input#username').setValue('testuser')
        await wrapper.find('input#password').setValue('password123')

        expect(wrapper.find('input#username').element.value).toBe('testuser')
        expect(wrapper.find('input#password').element.value).toBe('password123')
    })

    it('calls the auth store on form submission', async () => {
        // Spy on the authStore's login method
        const loginSpy = vi.spyOn(authStore, 'login').mockResolvedValue();

        const wrapper = mount(Login, {
            global: {
                stubs: {
                    RouterLink: true
                }
            }
        })

        await wrapper.find('input#username').setValue('testuser')
        await wrapper.find('input#password').setValue('password123')
        await wrapper.find('form').trigger('submit')

        // Assert that the spy was called with the correct credentials
        expect(loginSpy).toHaveBeenCalledWith({
            username: 'testuser',
            password: 'password123'
        })
    })

    it('displays an error message on failed login', async () => {
        // Mock the login method to reject with an error
        const expectedMessage = 'Login failed. Please check your username and password.';
        vi.spyOn(authStore, 'login').mockRejectedValue(new Error('any error'));

        const wrapper = mount(Login, {
            global: {
                stubs: {
                    RouterLink: true
                }
            }
        });

        await wrapper.find('input#username').setValue('wronguser');
        await wrapper.find('input#password').setValue('wrongpass');
        await wrapper.find('form').trigger('submit');

        // Wait for the DOM to update after the promise rejection
        await wrapper.vm.$nextTick();

        // Assert that the error message is displayed
        expect(wrapper.find('.alert-danger').exists()).toBe(true);
        expect(wrapper.find('.alert-danger').text()).toContain(expectedMessage);
    });

    it('redirects to the dashboard on successful login', async () => {
        // We should not mock the `login` method itself, but its dependencies.
        // Explicitly mock the implementation for this test to ensure it's applied correctly.
        axios.post.mockResolvedValue({ data: {} });

        // Mock `checkAuthStatus` to simulate a successful login, which sets isAuthenticated = true.
        vi.spyOn(authStore, 'checkAuthStatus').mockImplementation(async () => {
            authStore.isAuthenticated = true;
        });

        const wrapper = mount(Login, {
            global: {
                stubs: {
                    RouterLink: true
                }
            }
        });

        await wrapper.find('input#username').setValue('testuser');
        await wrapper.find('input#password').setValue('password123');
        await wrapper.find('form').trigger('submit');

        // Wait for all microtasks (promise resolutions) in the event loop to finish.
        // A zero-delay setTimeout is a robust way to do this.
        await new Promise(resolve => setTimeout(resolve, 0));

        // Assert that the router was called to redirect to the dashboard
        expect(router.push).toHaveBeenCalledWith({ name: 'Dashboard' });
    });
})
