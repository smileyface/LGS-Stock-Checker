import { describe, it, expect, beforeEach, vi, beforeAll } from 'vitest';
import SocketMock from 'socket.io-mock';

// 💡 FIX 1: REMOVE the module-level import of useSocket, _socket, and _internal. 
// We will load them dynamically later.

const mockListeners = {};

// This ensures the object exists synchronously for the factory to return it.
const globalMockSocketInstance = new SocketMock();

// Override the .on method of the globally created instance to store the listener function 
globalMockSocketInstance.on = vi.fn((event, handler) => {
    mockListeners[event] = handler;
});

// Add the necessary methods to the global instance
globalMockSocketInstance.connected = false;
globalMockSocketInstance.connect = vi.fn(() => { globalMockSocketInstance.connected = true; });
globalMockSocketInstance.disconnect = vi.fn(() => { globalMockSocketInstance.connected = false; });


// --- Setup for the Socket Mock (Synchronous and Stable) ---
// The synchronous factory guarantees the mock is ready before the target module loads.
vi.doMock('socket.io-client', () => {
    return {
        io: vi.fn(() => {
            // Return the one stable instance we created at module scope.
            return globalMockSocketInstance;
        }),
    };
});

/**
 * Helper function to manually invoke a registered listener on the mock socket, 
 * simulating a server-to-client event.
 */
function invokeSocketOn(eventName, data) {
    const listener = mockListeners[eventName];

    if (typeof listener === 'function') {
        listener(data);
    } else {
        // This confirms the listener was never registered on our mock.
        throw new Error(`No listener found for event: ${eventName}. Did useSocket run first?`);
    }
}

describe('useSocket Composable', () => {
    // 💡 FIX 2: Declare variables for the dynamically imported exports
    let trackedCards;
    let availabilityMap;
    let deleteCard;
    let saveCard;
    let updateCard;

    // Variables that hold the module exports, which we must assign in beforeAll
    let socket;
    let _internal;
    let useSocket;

    beforeAll(async () => {
        // 💡 FIX 3: DYNAMICALLY IMPORT the composable module AFTER the mock is stable.
        const composableModule = await import('../useSocket');

        // Assign module exports to our local variables
        useSocket = composableModule.useSocket;
        socket = composableModule._socket;
        _internal = composableModule._internal;

        // Call useSocket() ONCE to execute the module-level singleton logic
        const composable = useSocket();

        // Assign destructured composable exports
        trackedCards = composable.trackedCards;
        availabilityMap = composable.availabilityMap;
        deleteCard = composable.deleteCard;
        saveCard = composable.saveCard;
        updateCard = composable.updateCard;

        // Safety delay
        await new Promise(resolve => setTimeout(resolve, 0));
    });

    beforeEach(() => {
        // 1. Reset reactive state via internal exports
        // We now safely use _internal because it was assigned in beforeAll
        _internal.trackedCards.value = [];
        _internal.availabilityMap.value = {};

        // 2. Manually reset the socket connection state 
        // We now safely use the assigned socket variable
        socket.connected = false;

        // 3. Clear mock history (for spies on emit, connect, etc.)
        vi.clearAllMocks();
    });

    it('should connect and request initial data on first use', async () => {
        const emitSpy = vi.spyOn(socket, 'emit');

        // Simulate the client connecting (this triggers the listeners)
        socket.connect();
        invokeSocketOn('connect');

        expect(socket.connected).toBe(true);
        expect(emitSpy).toHaveBeenCalledWith('get_cards');
        expect(emitSpy).toHaveBeenCalledWith('get_card_availability');
    });

    it('should update trackedCards when receiving cards_data', async () => {
        const mockCardData = { tracked_cards: [{ card_name: 'Sol Ring', amount: 1 }] };

        // We only need the listener to be present here.
        invokeSocketOn('cards_data', mockCardData);

        expect(trackedCards.value).toEqual(mockCardData.tracked_cards);
    });

    it('should set availability status to "searching" on availability_check_started', async () => {
        const eventData = { card: 'Lightning Bolt' };

        invokeSocketOn('availability_check_started', eventData);

        expect(availabilityMap.value['Lightning Bolt']).toEqual({
            status: 'searching',
            stores: [],
        });
    });

    it('should update availabilityMap to "completed" on card_availability_data', async () => {
        const eventData = {
            card: 'Brainstorm',
            store: 'StoreA',
            items: [{ price: 1.99 }], // This makes it "available"
        };

        // This test will now find the listener registered by beforeAll
        invokeSocketOn('card_availability_data', eventData);

        expect(availabilityMap.value['Brainstorm']).toEqual({
            status: 'completed',
            stores: ['StoreA'],
        });
    });

    it('should call socket.emit when emitter functions are used', async () => {
        const emitSpy = vi.spyOn(socket, 'emit');
        // Ensure socket is connected for the emitters to run cleanly
        socket.connect();

        deleteCard('Sol Ring');
        expect(emitSpy).toHaveBeenCalledWith('delete_card', { card: 'Sol Ring' });

        const newCard = { card: 'New Card', amount: 1 };
        saveCard(newCard);
        expect(emitSpy).toHaveBeenCalledWith('add_card', newCard);

        const updatedCard = { card: 'Old Card', update_data: { amount: 2 } };
        updateCard(updatedCard);
        expect(emitSpy).toHaveBeenCalledWith('update_card', updatedCard);
    });
});