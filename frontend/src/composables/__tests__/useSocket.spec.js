import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useSocket } from '../useSocket';
import { io } from 'socket.io-client';
import SocketMock from 'socket.io-client-mock';

// Mock the 'socket.io-client' library
vi.mock('socket.io-client', () => {
    // The default export of the library is the `io` function.
    // We are replacing it with a constructor that returns a mock socket.
    return {
        io: vi.fn(() => new SocketMock()),
    };
});

describe('useSocket Composable', () => {
    let socket;

    beforeEach(() => {
        // Before each test, get a fresh instance of the mock socket
        // This is the same instance the composable will use because of the singleton pattern.
        socket = io();
        // Reset the composable's internal state if needed (though mocks handle this well)
    });

    it('should connect and request initial data on first use', () => {
        // The 'connect' event should be handled by the composable,
        // which then emits requests for data.
        const emitSpy = vi.spyOn(socket, 'emit');

        // First time calling useSocket will trigger the connection
        useSocket();
        socket.socket.emit('connect'); // Manually trigger the connect event on the mock

        expect(socket.connected).toBe(true);
        expect(emitSpy).toHaveBeenCalledWith('get_cards');
        expect(emitSpy).toHaveBeenCalledWith('get_card_availability');
    });

    it('should update trackedCards when receiving cards_data', () => {
        const { trackedCards } = useSocket();
        const mockCardData = { tracked_cards: [{ card_name: 'Sol Ring', amount: 1 }] };

        // Simulate the server sending data
        socket.socket.emit('cards_data', mockCardData);

        expect(trackedCards.value).toEqual(mockCardData.tracked_cards);
    });

    it('should set availability status to "searching" on availability_check_started', () => {
        const { availabilityMap } = useSocket();
        const eventData = { card: 'Lightning Bolt' };

        socket.socket.emit('availability_check_started', eventData);

        expect(availabilityMap.value['Lightning Bolt']).toEqual({
            status: 'searching',
            stores: [],
        });
    });

    it('should update availabilityMap to "completed" on card_availability_data', () => {
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

    it('should call socket.emit when emitter functions are used', () => {
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

