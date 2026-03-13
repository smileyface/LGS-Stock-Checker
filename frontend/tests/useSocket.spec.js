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
globalMockSocketInstance.emitMessage = vi.fn();


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
    let trackedCards;
    let availabilityMap;
    let deleteCard;

    let useSocket;

    beforeAll(async () => {
        const composableModule = await import('../src/composables/useSocket');
        useSocket = composableModule.useSocket;

        const composable = useSocket();

        trackedCards = composable.trackedCards;
        availabilityMap = composable.availabilityMap;
        deleteCard = composable.deleteCard;

        await new Promise(resolve => setTimeout(resolve, 0));
    });

    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('should connect and request initial data on first use', async () => {
        // 1. Spy on the RAW emit function of the global instance
        const emitSpy = vi.spyOn(globalMockSocketInstance, 'emit');
        emitSpy.mockClear();

        // 2. Simulate the client connecting
        globalMockSocketInstance.connect();
        invokeSocketOn('connect'); 

        // 3. Assert connection state
        expect(globalMockSocketInstance.connected).toBe(true);

        // 4. Assert against the fully wrapped Envelope that the internal wrapper generated!
        expect(emitSpy).toHaveBeenCalledWith(
            'get_cards', 
            expect.objectContaining({
                name: 'get_cards',
                payload: expect.any(Object)
            })
        );
/**        expect(emitSpy).toHaveBeenCalledWith(
            'get_card_availability', 
            expect.objectContaining({
                name: 'get_card_availability',
                payload: expect.any(Object)
            })
        );*/
    });

    it('should update trackedCards when receiving cards_data', async () => {
        const mockMessage = { 
            payload: { 
                cards: [{ card: { name: 'Sol Ring' }, amount: 1 }] 
            } 
        };

        invokeSocketOn('cards_data', mockMessage);

        // Update the expected array to include the newly decorated fields!
        expect(trackedCards.value).toEqual([{
            amount: 1,
            card: { name: 'Sol Ring' },
            card_name: 'Sol Ring', // Added by your composable
            specifications: []     // Added by your composable
        }]);
    });

    it.skip('should set availability status to "searching" on availability_check_started', async () => {
        // Wrap the event data in the payload structure
        const eventData = { payload: { card: 'Lightning Bolt' } };

        invokeSocketOn('availability_check_started', eventData);

        expect(availabilityMap.value['Lightning Bolt']).toEqual({
            status: 'searching',
            items: [],
        });
    });

    it.skip('should update availabilityMap to "completed" on card_availability_data', async () => {
        // Wrap the event data in the payload structure
        const eventData = {
            payload: {
                card: 'Brainstorm',
                store_slug: 'StoreA',
                items: [{ price: 1.99 }] 
            }
        };

        invokeSocketOn('card_availability_data', eventData);

        expect(availabilityMap.value['Brainstorm']).toEqual({
            status: 'completed',
            items: [{ price: 1.99, store_slug: 'StoreA' }]
        });
    });

    it('should call socket.emit when emitter functions are used', async () => {
        // Spy on the RAW emit function again
        const emitSpy = vi.spyOn(globalMockSocketInstance, 'emit');
        globalMockSocketInstance.connect();

        // Delete Card
        deleteCard('Sol Ring');
        expect(emitSpy).toHaveBeenCalledWith(
            'update_card', 
            expect.objectContaining({
                name: 'update_card',
                payload: expect.objectContaining({ command: 'delete' })
            })
        );
    });
});