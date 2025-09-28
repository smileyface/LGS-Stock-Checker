import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { mount } from '@vue/test-utils';
import AddCardModal from '../src/components/AddCardModal.vue';
import { Modal } from 'bootstrap';
import { io } from 'socket.io-client';

// --- Mocks ---

// Mock Bootstrap's Modal
const mockModalInstance = {
    show: vi.fn(),
    hide: vi.fn(),
};
vi.mock('bootstrap', () => ({
    Modal: vi.fn(() => mockModalInstance),
}));

// Mock Socket.IO client
const mockSocket = {
    on: vi.fn(),
    emit: vi.fn(),
};
vi.mock('socket.io-client', () => ({
    io: vi.fn(() => mockSocket),
}));


describe('AddCardModal.vue', () => {

    beforeEach(() => {
        // Use fake timers to control setTimeout for debouncing
        vi.useFakeTimers();
    });

    afterEach(() => {
        // Restore mocks and timers after each test
        vi.restoreAllMocks();
    });

    it('renders the form fields correctly', () => {
        const wrapper = mount(AddCardModal);

        expect(wrapper.find('h5.modal-title').text()).toBe('Add New Card');
        expect(wrapper.find('input#cardName').exists()).toBe(true);
        expect(wrapper.find('input#cardAmount').exists()).toBe(true);
        expect(wrapper.find('input#set_code').exists()).toBe(true);
        expect(wrapper.find('input#collector_number').exists()).toBe(true);
        expect(wrapper.find('select#finish').exists()).toBe(true);
    });

    it('emits "save-card" with the correct payload on submission', async () => {
        // Spy on hide to prevent side effects and only assert that it was called.
        const hideSpy = vi.spyOn(mockModalInstance, 'hide');

        const wrapper = mount(AddCardModal);

        // Simulate user input
        await wrapper.find('#cardName').setValue('Sol Ring');
        await wrapper.find('#cardAmount').setValue(4);
        await wrapper.find('#set_code').setValue('C21');

        // Trigger submission
        await wrapper.find('form').trigger('submit');

        // Assert that the event was emitted with the correct data
        expect(wrapper.emitted()).toHaveProperty('save-card');
        expect(wrapper.emitted('save-card')[0][0]).toEqual({
            card: 'Sol Ring',
            amount: 4,
            card_specs: {
                set_code: 'C21',
                collector_number: '',
                finish: 'non-foil'
            }
        });

        // Assert that the modal was hidden
        expect(hideSpy).toHaveBeenCalled();
    });

    it('resets the form after submission', async () => {
        const wrapper = mount(AddCardModal);

        // Fill the form
        await wrapper.find('#cardName').setValue('Test Card');
        await wrapper.find('#cardAmount').setValue(2);

        // Submit
        await wrapper.find('form').trigger('submit');

        // Assert form fields are reset
        expect(wrapper.find('#cardName').element.value).toBe('');
        expect(wrapper.find('#cardAmount').element.value).toBe('1');
    });

    it('emits a debounced "search_card_names" event when typing a card name', async () => {
        const wrapper = mount(AddCardModal);

        // Type in the input
        await wrapper.find('#cardName').setValue('Light');

        // The socket should not have been called yet due to debouncing
        expect(mockSocket.emit).not.toHaveBeenCalled();

        // Advance timers past the 300ms debounce period
        vi.advanceTimersByTime(301);

        // Now the event should have been emitted
        expect(mockSocket.emit).toHaveBeenCalledWith('search_card_names', { query: 'Light' });
    });

    it('updates datalist options when "card_name_search_results" is received', async () => {
        const wrapper = mount(AddCardModal);

        // Find the 'on' call for our event and capture the handler
        const onCall = mockSocket.on.mock.calls.find(call => call[0] === 'card_name_search_results');
        const eventHandler = onCall[1];

        // Simulate the server sending search results
        const searchResults = { card_names: ['Lightning Bolt', 'Lightning Greaves'] };
        eventHandler(searchResults);

        // Wait for Vue to update the DOM
        await wrapper.vm.$nextTick();

        const options = wrapper.findAll('datalist#cardNameDatalist option');
        expect(options.length).toBe(2);
        expect(options[0].attributes('value')).toBe('Lightning Bolt');
        expect(options[1].attributes('value')).toBe('Lightning Greaves');
    });
});