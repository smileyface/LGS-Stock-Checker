import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useSocket, _socket as socket, _internal } from '../useSocket';
import { io } from 'socket.io-client';

// Mock the 'socket.io-client' library
vi.mock('socket.io-client', async (importOriginal) => {
    // Dynamically import the mock to avoid hoisting issues with vi.mock
    const { default: SocketMock } = await import('socket.io-mock');
    const originalModule = await importOriginal();
    return {
        ...originalModule,
        // Replace the `io` function with a factory that returns an enhanced mock instance
        io: vi.fn(() => {
            const mockSocket = new SocketMock();
            // Add the missing `connect` method and `connected` property to the mock
            mockSocket.connected = false;
            mockSocket.connect = vi.fn(() => { mockSocket.connected = true; });

            // Add a `disconnect` method to allow for proper test cleanup
            mockSocket.disconnect = vi.fn(() => {
                mockSocket.connected = false;
            });
            return mockSocket;
        }),
    };
});

describe('useSocket Composable', () => {
    beforeEach(() => {
        // Reset the internal state before each test.
        _internal.trackedCards.value = [];
        _internal.availabilityMap.value = {};

        // Disconnect the socket to reset its `connected` flag.
        socket.disconnect();

        // Clear mock history to ensure assertions are clean.
        vi.clearAllMocks();
    });

    it('should connect and request initial data on first use', async () => {
        // Wait for the event loop to ensure the mock factory is complete.
        await new Promise(resolve => setTimeout(resolve, 0));

        // The 'connect' event should be handled by the composable,
        // which then emits requests for data
        const emitSpy = vi.spyOn(socket, 'emit');

        // Initialize the composable inside the test.
        useSocket();
        socket.socket.emit('connect'); // Manually trigger the 'connect' event from the mock server

        expect(socket.connected).toBe(true);
        expect(emitSpy).toHaveBeenCalledWith('get_cards');
        expect(emitSpy).toHaveBeenCalledWith('get_card_availability');
    });

    it('should update trackedCards when receiving cards_data', async () => {
        await new Promise(resolve => setTimeout(resolve, 0));
        const { trackedCards } = useSocket();
        const mockCardData = { tracked_cards: [{ card_name: 'Sol Ring', amount: 1 }] };

        // Simulate the server sending data
        socket.socket.emit('cards_data', mockCardData);

        expect(trackedCards.value).toEqual(mockCardData.tracked_cards);
    });

    it('should set availability status to "searching" on availability_check_started', async () => {
        await new Promise(resolve => setTimeout(resolve, 0));
        const { availabilityMap } = useSocket();
        const eventData = { card: 'Lightning Bolt' };

        socket.socket.emit('availability_check_started', eventData);

        expect(availabilityMap.value['Lightning Bolt']).toEqual({
            status: 'searching',
            stores: [],
        });
    });

    it('should update availabilityMap to "completed" on card_availability_data', async () => {
        await new Promise(resolve => setTimeout(resolve, 0));
        const { availabilityMap } = useSocket();
        const eventData = {
            card: 'Brainstorm',
            store: 'StoreA',
            items: [{ price: 1.99 }], // This makes it "available"
        };

        socket.socket.emit('card_availability_data', eventData);

        expect(availabilityMap.value['Brainstorm']).toEqual({
            status: 'completed',
            stores: ['StoreA'],
        });
    });

    it('should call socket.emit when emitter functions are used', async () => {
        await new Promise(resolve => setTimeout(resolve, 0));
        const { deleteCard, saveCard, updateCard } = useSocket();
        const emitSpy = vi.spyOn(socket, 'emit');

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
