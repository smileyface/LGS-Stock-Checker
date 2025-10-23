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
    // The default export is the Modal class
    Modal: vi.fn(() => mockModalInstance),
}));


describe('InStockModal.vue', () => {
    const cardNameProp = 'Sol Ring';
    const availableItemsProp = [
        { store_name: 'Store B', price: 5.99, set_code: 'LTC', collector_number: '350', finish: 'foil' },
        { store_name: 'Store A', price: 1.99, set_code: 'C21', collector_number: '125', finish: 'nonfoil' },
    ];

    let wrapper;

    beforeEach(() => {
        // Reset mocks before each test
        vi.clearAllMocks();

        // Mount the component for each test
        wrapper = mount(InStockModal, {
            props: {
                cardName: cardNameProp,
                availableItems: availableItemsProp,
            },
        });
    });

    it('renders the card name in the modal title', () => {
        expect(wrapper.find('.modal-title').text()).toContain('Available Stock: Sol Ring');
    });

    it('renders a list of available items', () => {
        const items = wrapper.findAll('.list-group-item');
        expect(items.length).toBe(2);

        // Check content of the first rendered item (which should be the cheapest due to default sort)
        const firstItemHtml = items[0].html();
        expect(firstItemHtml).toContain('Store A');
        expect(firstItemHtml).toContain('$1.99');
        expect(firstItemHtml).toContain('<strong>Set:</strong> C21');
        expect(firstItemHtml).toContain('<strong>#:</strong> 125');
        expect(firstItemHtml).toContain('<strong>Finish:</strong> nonfoil');
    });

    it('constructs the correct Scryfall image URL', () => {
        const image = wrapper.find('.list-group-item img');
        expect(image.attributes('src')).toBe('https://api.scryfall.com/cards/c21/125?format=image&version=normal');
    });

    it('displays a message when no items are available', async () => {
        await wrapper.setProps({ availableItems: [] });

        expect(wrapper.find('.list-group').exists()).toBe(false);
        expect(wrapper.find('.text-muted p').text()).toBe('No available stock details found.');
    });

    it('sorts items by price in ascending order by default', () => {
        const prices = wrapper.findAll('.fs-5.fw-bold');
        expect(prices[0].text()).toBe('$1.99');
        expect(prices[1].text()).toBe('$5.99');
    });

    it('toggles sort direction to descending when sort button is clicked', async () => {
        // Initial state check
        expect(wrapper.find('button.btn-outline-secondary').text()).toContain('▲');

        // Click to sort descending
        await wrapper.find('button.btn-outline-secondary').trigger('click');

        // Check button text and item order
        expect(wrapper.find('button.btn-outline-secondary').text()).toContain('▼');
        let prices = wrapper.findAll('.fs-5.fw-bold');
        expect(prices[0].text()).toBe('$5.99');
        expect(prices[1].text()).toBe('$1.99');

        // Click again to sort ascending
        await wrapper.find('button.btn-outline-secondary').trigger('click');

        // Check button text and item order
        expect(wrapper.find('button.btn-outline-secondary').text()).toContain('▲');
        prices = wrapper.findAll('.fs-5.fw-bold');
        expect(prices[0].text()).toBe('$1.99');
        expect(prices[1].text()).toBe('$5.99');
    });

    it('exposes a show method that calls the Bootstrap modal instance', () => {
        wrapper.vm.show();
        expect(mockModalInstance.show).toHaveBeenCalledTimes(1);
    });

    it('resets the sort direction to ascending when the modal is shown', async () => {
        // 1. Manually set the sort direction to descending
        await wrapper.find('button.btn-outline-secondary').trigger('click');
        expect(wrapper.vm.sortDirection).toBe('desc');

        // 2. Call the show method
        wrapper.vm.show();

        // 3. Assert that the sort direction was reset
        expect(wrapper.vm.sortDirection).toBe('asc');
    });
});