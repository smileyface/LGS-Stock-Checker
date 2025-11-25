import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount } from '@vue/test-utils';
import InStockModal from '../src/components/InStockModal.vue';

// --- Mocks ---

// Mock Bootstrap's Modal to control its behavior and spy on its methods
const mockModalInstance = {
    show: vi.fn(),
    hide: vi.fn(),
};
vi.mock('bootstrap', () => ({
// Mock the Modal as a class that returns our instance
    Modal: class {
        constructor() {
            return mockModalInstance;
        }
    }
}));


describe('InStockModal.vue', () => {
    const cardNameProp = 'Sol Ring';
    const availableItemsProp = [
        { store_name: 'Store B', price: 5.99, set_code: 'LTC', collector_number: '350', finish: 'foil' },
        { store_name: 'Store A', price: 1.99, set_code: 'C21', collector_number: '125', finish: 'non-foil' },
    ]; // Note: The component doesn't use all these fields anymore.

    let wrapper;

    beforeEach(() => {
        // Reset mocks before each test
        vi.clearAllMocks();

        // Mount the component for each test
        wrapper = mount(InStockModal, {
            props: {
                cardName: cardNameProp,
                items: availableItemsProp, // Prop name is 'items'
            },
        });
    });

    it('renders the card name in the modal title', () => {
        expect(wrapper.find('.modal-title').text()).toContain('Stock for: Sol Ring');
    });

    it('renders a list of available items', () => {
        const items = wrapper.findAll('.list-group-item');
        expect(items.length).toBe(2);

        const firstItemText = items[0].text();
        expect(firstItemText).toContain('Store A');
        expect(firstItemText).toContain('$1.99');
        expect(firstItemText).toContain('Set: C21');
    });
    it('displays a message when no items are available', async () => {
        // Mount a new wrapper to ensure clean state
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

    it('exposes a show method that calls the Bootstrap modal instance', () => {
        wrapper.vm.show();
        expect(mockModalInstance.show).toHaveBeenCalledTimes(1);
    });

});