import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { mount } from '@vue/test-utils';
import { ref } from 'vue';
import AddCardModal from '../src/components/AddCardModal.vue';

// --- Mocks ---

// 1. DEFINE the mock object here. It must include .off()
const mockSocket = {
    on: vi.fn(),
    emit: vi.fn(),
    off: vi.fn(), // This is crucial for component unmount
};

// 2. USE the mock object. This runs once and is stable.
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
    
    // 3. RESET the history of the mocks before each test
    beforeEach(() => {
        vi.clearAllMocks();
    });

    // 4. RESTORE real timers after each test
    afterEach(() => {
        vi.useRealTimers();
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

        await wrapper.find('#cardName').setValue('Sol Ring');
        await wrapper.find('#amount').setValue(4);
        
        await wrapper.vm.handleSave();

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
        expect(wrapper.emitted()).toHaveProperty('close');
    });

    // 5. This test needs REAL timers (the default) to use await $nextTick
    it("updates searchResults ref when 'card_name_search_results' is received", async () => {
        const wrapper = mount(AddCardModal);
        
        // Wait for the onMounted() hook to run
        await wrapper.vm.$nextTick(); 

        // Find the 'on' call for our event and capture the handler
        const onCall = mockSocket.on.mock.calls.find(call => call[0] === 'card_name_search_results');
        const eventHandler = onCall[1];

        // Simulate the server sending search results
        const searchResultsData = { card_names: ['Lightning Bolt', 'Lightning Greaves'] };
        eventHandler(searchResultsData);
        
        // Wait for Vue to process the state update
        await wrapper.vm.$nextTick(); 

        // Now the assertion will see the updated state
        expect(wrapper.vm.searchResults).toEqual(['Lightning Bolt', 'Lightning Greaves']);
    });

    // 6. This test needs FAKE timers
    it("emits a debounced 'search_card_names' event when typing a card name", async () => {
        // --- Enable fake timers just for this test ---
        vi.useFakeTimers();

        const wrapper = mount(AddCardModal, { props: { show: true } });
        await wrapper.vm.$nextTick(); // Wait for onMounted

        // Type in the input
        await wrapper.find('#cardName').setValue('Light');

        // The socket should not have been called yet due to debouncing
        expect(mockSocket.emit).not.toHaveBeenCalled();

        // Advance timers past the 300ms debounce period
        vi.advanceTimersByTime(301);

        // Now the event should have been emitted
        expect(mockSocket.emit).toHaveBeenCalledWith('search_card_names', { query: 'Light' });
    });
});