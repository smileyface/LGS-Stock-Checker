import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { mount } from '@vue/test-utils';
import { ref } from 'vue';
import AddCardModal from '../src/components/AddCardModal.vue';

// --- Updated Mocks ---
const mockSocket = {
    on: vi.fn(),
    emit: vi.fn(),
    off: vi.fn(),
    emitMessage: vi.fn(), // ADD THIS
};

vi.mock('../src/composables/useSocket', () => ({
    useSocket: vi.fn(() => ({
        socket: mockSocket,
        emitMessage: mockSocket.emitMessage, // Map it here
        off: mockSocket.off
    })),
}));

vi.mock('../src/composables/useCardPrintings', () => ({
    useCardPrintings: vi.fn(() => ({
        setOptions: ref([]),
        collectorNumberOptions: ref([]),
        finishOptions: ref([]),
    })),
}));

describe('AddCardModal.vue', () => {
    
    beforeEach(() => {
        vi.clearAllMocks();
    });

    afterEach(() => {
        vi.useRealTimers();
    });

    it('renders the form fields correctly', () => {
        const wrapper = mount(AddCardModal);
        expect(wrapper.find('input#cardName').exists()).toBe(true);
        expect(wrapper.find('input#amount').exists()).toBe(true);
    });

    it("emits 'update_card' message to socket on submission", async () => {
        const wrapper = mount(AddCardModal);

        await wrapper.find('#cardName').setValue('Sol Ring');
        await wrapper.find('#amount').setValue(4);
        
        await wrapper.vm.handleSave();

        // Check that the socket was called, NOT the Vue emit
        expect(mockSocket.emitMessage).toHaveBeenCalledWith('update_card', expect.objectContaining({
            command: 'add',
            update_data: expect.objectContaining({
                amount: 4,
                card: { name: 'Sol Ring' }
            })
        }));
        
        expect(wrapper.emitted()).toHaveProperty('close');
    });

    it("updates searchResults ref when 'card_name_search_results' is received", async () => {
        const wrapper = mount(AddCardModal);
        await wrapper.vm.$nextTick(); 

        const onCall = mockSocket.on.mock.calls.find(call => call[0] === 'card_name_search_results');
        const eventHandler = onCall[1];

        // Ensure this matches your data.card_names key in the component!
        const searchResultsData = { card_names: ['Lightning Bolt', 'Lightning Greaves'] };
        eventHandler(searchResultsData);
        
        await wrapper.vm.$nextTick(); 
        expect(wrapper.vm.searchResults).toEqual(['Lightning Bolt', 'Lightning Greaves']);
    });

    it("emits a debounced 'search_card_names' message", async () => {
        vi.useFakeTimers();
        const wrapper = mount(AddCardModal);

        await wrapper.find('#cardName').setValue('Light');
        expect(mockSocket.emitMessage).not.toHaveBeenCalled();

        vi.advanceTimersByTime(301);

        // Assert against emitMessage
        expect(mockSocket.emitMessage).toHaveBeenCalledWith('search_card_names', { query: 'Light' });
    });

    it('displays an error message if the card name is empty on save', async () => {
        const wrapper = mount(AddCardModal);
        
        // 1. Manually set the cardName to empty string just to be sure
        wrapper.vm.cardName = '';

        // 2. Call the method directly via the VM
        await wrapper.vm.handleSave();
        
        // 3. Wait for the DOM to catch up
        await wrapper.vm.$nextTick(); 
        
        // 4. Debug: if it still fails, let's see what the HTML actually looks like
        // console.log(wrapper.html());

        const errorAlert = wrapper.find('.alert-danger');
        expect(errorAlert.exists()).toBe(true);
        expect(errorAlert.text()).toContain('Card name is required');
        
        expect(mockSocket.emitMessage).not.toHaveBeenCalled();
    });

    it('unregisters socket listeners when destroyed', () => {
        const wrapper = mount(AddCardModal);
        wrapper.unmount();
        
        // Ensure .off() was called for the specific search event
        expect(mockSocket.off).toHaveBeenCalledWith('card_name_search_results');
    });
});