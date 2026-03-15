import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount } from '@vue/test-utils';
import InStockModal from '../src/components/InStockModal.vue';

// --- Mocks ---

// 1. Mock Bootstrap Modal
const mockModalInstance = {
    show: vi.fn(),
    hide: vi.fn(),
    dispose: vi.fn(), // Added dispose since your component calls it on unmount!
};
vi.mock('bootstrap', () => ({
    Modal: class {
        constructor() {
            return mockModalInstance;
        }
    }
}));

// 2. Mock the Socket Composable
const mockSocketOn = vi.fn();
const mockSocketOff = vi.fn();
const mockGetStockData = vi.fn();

vi.mock('@/composables/useSocket', () => ({
    useSocket: vi.fn(() => ({
        socket: {
            on: mockSocketOn,
            off: mockSocketOff
        },
        getStockData: mockGetStockData
    }))
}));

describe('InStockModal.vue', () => {
    const cardNameProp = 'Sol Ring';
    const availableItemsProp = [
        { store_name: 'Store B', price: 5.99, set_code: 'LTC', quantity: 1 },
        { store_name: 'Store A', price: 1.99, set_code: 'C21', quantity: 4 },
    ]; 

    let wrapper;

    beforeEach(() => {
        vi.clearAllMocks();

        wrapper = mount(InStockModal, {
            props: {
                cardName: cardNameProp,
                items: availableItemsProp,
            },
        });
    });

    it('renders the card name in the modal title', () => {
        expect(wrapper.find('.modal-title').text()).toContain('Stock for: Sol Ring');
    });

    it('renders a list of available items', () => {
        const items = wrapper.findAll('.list-group-item');
        expect(items.length).toBe(2);

        // Because it sorts by price automatically, Store A ($1.99) should be first
        const firstItemText = items[0].text();
        expect(firstItemText).toContain('Store A');
        expect(firstItemText).toContain('$1.99');
        expect(firstItemText).toContain('Set: C21');
    });

    it('displays a message when no items are available', async () => {
        const emptyWrapper = mount(InStockModal, {
            props: { cardName: cardNameProp, items: [] }
        });

        expect(emptyWrapper.find('.list-group').exists()).toBe(false);
        expect(emptyWrapper.find('.text-center p').text()).toBe('No stock found for this card in your selected stores.');
    });

    it('sorts items by price in ascending order by default', () => {
        const prices = wrapper.findAll('.fs-5.fw-bold');
        expect(prices.length).toBe(2);
        expect(prices[0].text()).toBe('$1.99');
        expect(prices[1].text()).toBe('$5.99');
    });

    it('exposes a show method that calls the Bootstrap modal and requests stock data', () => {
        wrapper.vm.show();
        
        // Verifies Bootstrap modal opened
        expect(mockModalInstance.show).toHaveBeenCalledTimes(1);
        
        // Verifies it asked the backend for fresh data
        expect(mockGetStockData).toHaveBeenCalledTimes(1);
        expect(mockGetStockData).toHaveBeenCalledWith('Sol Ring');
    });

    it('registers and cleans up socket listeners', () => {
        // Assert it registered on mount
        expect(mockSocketOn).toHaveBeenCalledWith('stock_data', expect.any(Function));

        // Unmount the component
        wrapper.unmount();

        // Assert it cleaned up
        expect(mockSocketOff).toHaveBeenCalledWith('stock_data');
        expect(mockModalInstance.dispose).toHaveBeenCalledTimes(1);
    });
});