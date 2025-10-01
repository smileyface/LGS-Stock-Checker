import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { mount } from '@vue/test-utils';
import Register from '../src/views/Register.vue';
import { authStore } from '../src/stores/auth';

// Mock the authStore to isolate the component
vi.mock('../src/stores/auth', () => ({
    authStore: {
        register: vi.fn(),
    },
}));

describe('Register.vue', () => {
    let wrapper;

    beforeEach(() => {
        // Reset mocks and mount the component before each test
        vi.clearAllMocks();
        wrapper = mount(Register, {
            global: {
                stubs: {
                    // Stub RouterLink to prevent warnings about missing router context
                    RouterLink: true,
                },
            },
        });
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    it('renders the registration form correctly', () => {
        expect(wrapper.find('h3').text()).toBe('Register New Account');
        expect(wrapper.find('input#username').exists()).toBe(true);
        expect(wrapper.find('input#password').exists()).toBe(true);
        expect(wrapper.find('input#confirmPassword').exists()).toBe(true);
        expect(wrapper.find('button[type="submit"]').text()).toBe('Register');
    });

    it('allows user to type into input fields', async () => {
        await wrapper.find('#username').setValue('newuser');
        await wrapper.find('#password').setValue('newpass123');
        await wrapper.find('#confirmPassword').setValue('newpass123');

        expect(wrapper.find('#username').element.value).toBe('newuser');
        expect(wrapper.find('#password').element.value).toBe('newpass123');
        expect(wrapper.find('#confirmPassword').element.value).toBe('newpass123');
    });

    it('shows an error if passwords do not match', async () => {
        await wrapper.find('#username').setValue('newuser');
        await wrapper.find('#password').setValue('password123');
        await wrapper.find('#confirmPassword').setValue('password456');

        await wrapper.find('form').trigger('submit');

        expect(authStore.register).not.toHaveBeenCalled();
        expect(wrapper.find('.alert-danger').exists()).toBe(true);
        expect(wrapper.find('.alert-danger').text()).toBe('Passwords do not match.');
    });

    it('calls authStore.register on successful submission', async () => {
        const credentials = {
            username: 'newuser',
            password: 'password123',
        };

        // Mock the register function to resolve successfully
        authStore.register.mockResolvedValue();

        await wrapper.find('#username').setValue(credentials.username);
        await wrapper.find('#password').setValue(credentials.password);
        await wrapper.find('#confirmPassword').setValue(credentials.password);

        await wrapper.find('form').trigger('submit');

        expect(authStore.register).toHaveBeenCalledWith(credentials);
        // The component should not show an error on success
        expect(wrapper.find('.alert-danger').exists()).toBe(false);
    });

    it('displays an error message on registration failure', async () => {
        const errorMessage = 'Username already exists';
        // Mock the register function to simulate a backend error
        authStore.register.mockRejectedValue({
            response: {
                data: {
                    error: errorMessage,
                },
            },
        });

        await wrapper.find('#username').setValue('existinguser');
        await wrapper.find('#password').setValue('password123');
        await wrapper.find('#confirmPassword').setValue('password123');

        await wrapper.find('form').trigger('submit');

        // Wait for the next DOM update cycle for the error to appear
        await wrapper.vm.$nextTick();

        expect(wrapper.find('.alert-danger').exists()).toBe(true);
        expect(wrapper.find('.alert-danger').text()).toBe(errorMessage);
    });
});
