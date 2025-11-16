import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { mount } from '@vue/test-utils';
import { ref } from 'vue';
import AddCardModal from '../src/components/AddCardModal.vue';

// --- Mocks ---

// Mock the useSocket composable
const mockSocket = {
    on: vi.fn(),
    emit: vi.fn(),
};
vi.mock('../src/composables/useSocket', () => ({
    useSocket: vi.fn(() => ({
        socket: mockSocket,
    })),
}));

// Mock the useCardPrintings composable
vi.mock('../src/composables/useCardPrintings', () => ({
    useCardPrintings: vi.fn(() => ({
        setOptions: ref([]),
        collectorNumberOptions: ref([]),
        finishOptions: ref([]),
    })),
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

        expect(wrapper.find('input#cardName').exists()).toBe(true);
        expect(wrapper.find('input#amount').exists()).toBe(true);
        expect(wrapper.find('select#set').exists()).toBe(true);
        expect(wrapper.find('select#collectorNumber').exists()).toBe(true);
        expect(wrapper.find('select#finish').exists()).toBe(true);
    });

    it("emits 'save-card' with the correct payload on submission", async () => {
        const wrapper = mount(AddCardModal, { props: { show: true } });

        // Simulate user input
        await wrapper.find('#cardName').setValue('Sol Ring');
        await wrapper.find('#amount').setValue(4);
        // Note: We are not testing the dependent dropdowns here, just the save logic.
        // We can assume selectedSet, etc., are empty strings.

        // Trigger submission by calling the handler
        await wrapper.vm.handleSave();

        // Assert that the event was emitted with the correct data
        expect(wrapper.emitted()).toHaveProperty('save-card');
        expect(wrapper.emitted('save-card')[0][0]).toEqual({
            card: 'Sol Ring',
            amount: 4,
            card_specs: {
                set_code: '',
                collector_number: '',
                finish: ''
            }
        });

        // Assert that the close event was also emitted
        expect(wrapper.emitted()).toHaveProperty('close');
    });

    it("updates searchResults ref when 'card_name_search_results' is received", async () => {
        const wrapper = mount(AddCardModal);

        // Find the 'on' call for our event and capture the handler
        const onCall = mockSocket.on.mock.calls.find(call => call[0] === 'card_name_search_results');
        const eventHandler = onCall[1];

        // Simulate the server sending search results
        const searchResultsData = { card_names: ['Lightning Bolt', 'Lightning Greaves'] };
        eventHandler(searchResultsData);

        // No need to wait for DOM update, just check the component's internal state
        expect(wrapper.vm.searchResults).toEqual(['Lightning Bolt', 'Lightning Greaves']);
    });

    it("emits a debounced 'search_card_names' event when typing a card name", async () => {
        const wrapper = mount(AddCardModal, { props: { show: true } });

        // Type in the input
        await wrapper.find('#cardName').setValue('Light');

        // The socket should not have been called yet due to debouncing
        expect(mockSocket.emit).not.toHaveBeenCalled();

        // Advance timers past the 300ms debounce period
        vi.advanceTimersByTime(301);

        // Now the event should have been emitted
        expect(mockSocket.emit).toHaveBeenCalledWith('search_card_names', { query: 'Light' });
    });

    it("updates datalist options when 'card_name_search_results' is received", async () => {
        const wrapper = mount(AddCardModal, { props: { show: true } });

        // Find the 'on' call for our event and capture the handler
        const onCall = mockSocket.on.mock.calls.find(call => call[0] === 'card_name_search_results'
        );
        const eventHandler = onCall[1];

        // Simulate the server sending search results
        const searchResultsData = { card_names: ['Lightning Bolt', 'Lightning Greaves'] };
        eventHandler(searchResultsData);

        // Wait for Vue to update the DOM
        await wrapper.vm.$nextTick();

        const options = wrapper.findAll('datalist#cardNameDatalist option');
        expect(options.length).toBe(2);
        expect(options[0].attributes('value')).toBe('Lightning Bolt');
        expect(options[1].attributes('value')).toBe('Lightning Greaves');
    });
});