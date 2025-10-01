import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { mount } from '@vue/test-utils';
import { ref } from 'vue';
import { useCardPrintings } from '../src/composables/useCardPrintings';
import { useSocket } from '../src/composables/useSocket';

// --- Mocks ---

// Mock the useSocket composable to control the socket behavior
const mockSocket = {
    on: vi.fn(),
    off: vi.fn(),
    emit: vi.fn(),
};
vi.mock('../src/composables/useSocket', () => ({
    useSocket: vi.fn(() => ({
        socket: mockSocket,
    })),
}));

// --- Test Data ---
const mockPrintingsData = {
    card_name: 'Sol Ring',
    printings: [
        { set_code: 'C21', collector_number: '125', finishes: ['nonfoil', 'foil'] },
        { set_code: 'LTC', collector_number: '3', finishes: ['nonfoil', 'etched'] },
        { set_code: 'LTC', collector_number: '350', finishes: ['foil'] },
    ],
};


describe('useCardPrintings.js', () => {
    let cardNameRef;
    let selectedSetRef;
    let selectedCollectorNumberRef;

    // Helper to mount a dummy component to test the composable's lifecycle
    const mountComposable = () => {
        let composableResult;
        const TestComponent = {
            template: '<div></div>',
            setup() {
                composableResult = useCardPrintings(cardNameRef, selectedSetRef, selectedCollectorNumberRef);
                return {};
            },
        };
        mount(TestComponent);
        return composableResult;
    };

    beforeEach(() => {
        // Reset refs for each test
        cardNameRef = ref('');
        selectedSetRef = ref('');
        selectedCollectorNumberRef = ref('');
    });

    afterEach(() => {
        // Clear all mocks after each test
        vi.clearAllMocks();
    });

    it('registers and unregisters the socket listener on mount/unmount', () => {
        const wrapper = mount({
            template: '<div></div>',
            setup() {
                useCardPrintings(cardNameRef, selectedSetRef, selectedCollectorNumberRef);
                return {};
            },
        });

        expect(mockSocket.on).toHaveBeenCalledWith('card_printings_data', expect.any(Function));

        wrapper.unmount();
        expect(mockSocket.off).toHaveBeenCalledWith('card_printings_data', expect.any(Function));
    });

    it('fetches printings when cardNameRef changes', async () => {
        mountComposable();

        cardNameRef.value = 'Sol Ring';
        await new Promise(resolve => setTimeout(resolve, 0)); // Wait for watcher

        expect(mockSocket.emit).toHaveBeenCalledWith('get_card_printings', { card_name: 'Sol Ring' });
    });

    it('updates printings ref when matching data is received', () => {
        const { printings } = mountComposable();
        cardNameRef.value = 'Sol Ring';

        // Find the handler function registered by the composable
        const onCall = mockSocket.on.mock.calls.find(call => call[0] === 'card_printings_data');
        const eventHandler = onCall[1];

        // Simulate server sending data
        eventHandler(mockPrintingsData);

        expect(printings.value).toEqual(mockPrintingsData.printings);
    });

    it('does NOT update printings ref if data is for a different card', () => {
        const { printings } = mountComposable();
        cardNameRef.value = 'Thoughtseize'; // We are interested in a different card

        const onCall = mockSocket.on.mock.calls.find(call => call[0] === 'card_printings_data');
        const eventHandler = onCall[1];

        // Simulate server sending data for 'Sol Ring'
        eventHandler(mockPrintingsData);

        expect(printings.value).toEqual([]); // Should remain empty
    });

    it('computes setOptions correctly from printings', () => {
        const { setOptions, printings } = mountComposable();
        printings.value = mockPrintingsData.printings;

        // Should contain unique set codes
        expect(setOptions.value).toEqual(['C21', 'LTC']);
    });

    it('computes collectorNumberOptions based on selectedSetRef', () => {
        const { collectorNumberOptions, printings } = mountComposable();
        printings.value = mockPrintingsData.printings;

        // Initially empty
        expect(collectorNumberOptions.value).toEqual([]);

        // Select a set
        selectedSetRef.value = 'LTC';
        expect(collectorNumberOptions.value).toEqual(['3', '350']);
    });

    it('computes finishOptions based on selectedSetRef and selectedCollectorNumberRef', () => {
        const { finishOptions, printings } = mountComposable();
        printings.value = mockPrintingsData.printings;

        // Select set and collector number
        selectedSetRef.value = 'LTC';
        selectedCollectorNumberRef.value = '3';

        expect(finishOptions.value).toEqual(['nonfoil', 'etched']);
    });
});
