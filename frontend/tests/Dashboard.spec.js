import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount } from '@vue/test-utils';
import { ref, readonly } from 'vue';
import Dashboard from '../src/views/Dashboard.vue';
import { useSocket } from '../src/composables/useSocket';

// Mock the entire composable
// Correctly mock the module to return a mock function for useSocket
vi.mock('../src/composables/useSocket', () => ({
    useSocket: vi.fn(), // This creates a mock function that can be spied on and have its return value set
}));

// Mock child components to isolate the Dashboard component
const mockEditModalShow = vi.fn();
const mockInStockModalShow = vi.fn();
const AddCardModal = { template: '<div class="add-card-modal-mock"></div>' };
const EditCardModal = {
    template: '<div class="edit-card-modal-mock"></div>',
    // To correctly simulate a <script setup> component with defineExpose,
    // we need a setup function that returns the methods to be exposed.
    setup() {
        return { show: mockEditModalShow };
    }
};
const InStockModal = {
    template: '<div class="in-stock-modal-mock"></div>',
    setup() {
        return { show: mockInStockModalShow };
    }
};
const BaseLayout = { template: '<div><slot /></div>' };

describe('Dashboard.vue', () => {
    // Create reactive refs that our mock will use
    const trackedCards = ref([]);
    const availabilityMap = ref({});
    let wrapper;

    beforeEach(() => {
        // Reset state before each test
        mockEditModalShow.mockClear();
        mockInStockModalShow.mockClear();
        trackedCards.value = [];
        availabilityMap.value = {};

        // Provide the mock implementation for useSocket
        useSocket.mockReturnValue({
            trackedCards: readonly(trackedCards),
            availabilityMap: readonly(availabilityMap),
            deleteCard: vi.fn(),
            saveCard: vi.fn(),
            updateCard: vi.fn(),
        });
        useSocket().getStockData = vi.fn(); // Mock getStockData separately for this test

        // Mount the component once for all tests in this block
        wrapper = mount(Dashboard, {
            global: {
                stubs: { AddCardModal, EditCardModal, InStockModal, BaseLayout }
            }
        });
    });

    it('renders a list of tracked cards', async () => {
        trackedCards.value = [
            { card_name: 'Sol Ring', amount: 1, specifications: [] },
            { card_name: 'Brainstorm', amount: 4, specifications: [] },
        ];
        await wrapper.vm.$nextTick(); // Wait for DOM to update

        const rows = wrapper.findAll('tbody tr');
        expect(rows.length).toBe(2);
        expect(wrapper.text()).toContain('Sol Ring');
        expect(wrapper.text()).toContain('Brainstorm');
    });

    it('renders "Searching" badge when availability status is searching', async () => {
        const cardName = 'Lightning Bolt';
        trackedCards.value = [{ card_name: cardName, amount: 4 }];
        availabilityMap.value = { [cardName]: { status: 'searching', stores: [] } };
        await wrapper.vm.$nextTick();

        const searchingBadge = wrapper.find('.badge.bg-info');
        expect(searchingBadge.exists()).toBe(true);
        expect(searchingBadge.text()).toContain('Searching');
    });

    it('renders "Available" badge when card is available', async () => {
        const cardName = 'Swords to Plowshares';
        trackedCards.value = [{ card_name: cardName, amount: 2 }];
        availabilityMap.value = { [cardName]: { status: 'completed', items: [{ price: 1.99 }] } };
        await wrapper.vm.$nextTick();

        const availableBadge = wrapper.find('.badge.bg-success');
        expect(availableBadge.exists()).toBe(true);
        expect(availableBadge.text()).toBe('Available');
    });

    it('renders "Not Available" badge when card is not available', async () => {
        const cardName = 'Dark Ritual';
        trackedCards.value = [{ card_name: cardName, amount: 4 }];
        availabilityMap.value = { [cardName]: { status: 'completed', items: [] } };
        await wrapper.vm.$nextTick();

        const availabilityCell = wrapper.find('tbody tr td:last-child');
        expect(availabilityCell.html()).toContain('badge bg-secondary');
        expect(availabilityCell.text()).toBe('Not Available');
    });

    it('calls deleteCard from composable when delete button is clicked', async () => {
        const cardName = 'Sol Ring';
        trackedCards.value = [{ card_name: cardName, amount: 1 }];
        await wrapper.vm.$nextTick();
        const { deleteCard } = useSocket(); // Get the mock function after it's been set up

        await wrapper.find('button[title="Delete"]').trigger('click');

        expect(deleteCard).toHaveBeenCalledTimes(1);
        expect(deleteCard).toHaveBeenCalledWith(cardName);
    });

    it('opens the edit modal with the correct card when edit button is clicked', async () => {
        const cardToEdit = { card_name: 'Sol Ring', amount: 1, specifications: [] };
        trackedCards.value = [cardToEdit];
        await wrapper.vm.$nextTick();

        // Find the edit button and click it
        await wrapper.find('button[title="Edit"]').trigger('click');

        // Assert that the component's `cardToEdit` ref is set
        // This requires accessing the internal vm state
        expect(wrapper.vm.cardToEdit).toEqual(cardToEdit);

        // Assert that the modal's show method was called
        // The component uses nextTick internally before calling show()
        await wrapper.vm.$nextTick();
        expect(mockEditModalShow).toHaveBeenCalledTimes(1);
    });

    it("opens the in-stock modal on double-clicking an 'Available' badge", async () => {
        const cardName = 'Brainstorm';
        const availableItems = [{ store_name: 'Store A', price: 0.99, set_code: 'ICE', collector_number: '1', finish: 'non-foil' }];
        trackedCards.value = [{ card_name: cardName, amount: 4, specifications: [] }];
        availabilityMap.value = { [cardName]: { status: 'completed', items: availableItems } };
        await wrapper.vm.$nextTick();

        // Find the "Available" badge and trigger a double-click
        const availableBadge = wrapper.find('.badge.bg-success');
        await availableBadge.trigger('dblclick');

        // Assert that the component's state was updated correctly
        expect(wrapper.vm.selectedCardForStock).toBe(cardName);
        expect(wrapper.vm.availableItemsForModal).toEqual(availableItems);

        // Assert that the modal's show method was called. This requires waiting for the nextTick
        // that is used inside the showInStockModal function.
        await wrapper.vm.$nextTick();
        expect(mockInStockModalShow).toHaveBeenCalledTimes(1);
    });
});
