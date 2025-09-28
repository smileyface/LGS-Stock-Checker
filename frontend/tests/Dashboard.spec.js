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
const AddCardModal = { template: '<div class="add-card-modal-mock"></div>' };
const EditCardModal = { template: '<div class="edit-card-modal-mock"></div>' };
const BaseLayout = { template: '<div><slot /></div>' };

describe('Dashboard.vue', () => {
    // Create reactive refs that our mock will use
    const trackedCards = ref([]);
    const availabilityMap = ref({});

    beforeEach(() => {
        // Reset state before each test
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
    });

    it('renders a list of tracked cards', () => {
        trackedCards.value = [
            { card_name: 'Sol Ring', amount: 1, specifications: [] },
            { card_name: 'Brainstorm', amount: 4, specifications: [] },
        ];

        const wrapper = mount(Dashboard, {
            global: {
                stubs: { AddCardModal, EditCardModal, BaseLayout }
            }
        });

        const rows = wrapper.findAll('tbody tr');
        expect(rows.length).toBe(2);
        expect(wrapper.text()).toContain('Sol Ring');
        expect(wrapper.text()).toContain('Brainstorm');
    });

    it('renders "Searching" badge when availability status is searching', () => {
        const cardName = 'Lightning Bolt';
        trackedCards.value = [{ card_name: cardName, amount: 4 }];
        availabilityMap.value = { [cardName]: { status: 'searching', stores: [] } };

        const wrapper = mount(Dashboard, { global: { stubs: { AddCardModal, EditCardModal, BaseLayout } } });

        const availabilityCell = wrapper.find('tbody tr td:last-child');
        expect(availabilityCell.html()).toContain('spinner-border');
        expect(availabilityCell.text()).toContain('Searching');
    });

    it('renders "Available" badge when card is available', () => {
        const cardName = 'Swords to Plowshares';
        trackedCards.value = [{ card_name: cardName, amount: 2 }];
        availabilityMap.value = { [cardName]: { status: 'completed', stores: ['StoreA'] } };

        const wrapper = mount(Dashboard, { global: { stubs: { AddCardModal, EditCardModal, BaseLayout } } });

        const availabilityCell = wrapper.find('tbody tr td:last-child');
        expect(availabilityCell.html()).toContain('badge bg-success');
        expect(availabilityCell.text()).toBe('Available');
    });

    it('renders "Not Available" badge when card is not available', () => {
        const cardName = 'Dark Ritual';
        trackedCards.value = [{ card_name: cardName, amount: 4 }];
        availabilityMap.value = { [cardName]: { status: 'completed', stores: [] } };

        const wrapper = mount(Dashboard, { global: { stubs: { AddCardModal, EditCardModal, BaseLayout } } });

        const availabilityCell = wrapper.find('tbody tr td:last-child');
        expect(availabilityCell.html()).toContain('badge bg-secondary');
        expect(availabilityCell.text()).toBe('Not Available');
    });

    it('calls deleteCard from composable when delete button is clicked', async () => {
        const { deleteCard } = useSocket();
        const cardName = 'Sol Ring';
        trackedCards.value = [{ card_name: cardName, amount: 1 }];

        const wrapper = mount(Dashboard, { global: { stubs: { AddCardModal, EditCardModal, BaseLayout } } });

        await wrapper.find('button[title="Delete"]').trigger('click');

        expect(deleteCard).toHaveBeenCalledTimes(1);
        expect(deleteCard).toHaveBeenCalledWith(cardName);
    });
});
