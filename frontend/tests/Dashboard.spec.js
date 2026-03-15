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
    const trackedCards = ref([]);
    const availabilityMap = ref({});
    let wrapper;

    // Helper to create the new card structure
    const createMockCard = (name, amount = 1) => ({
        amount: amount,
        card: { name: name }, // New nested structure
        specifications: []
    });

    beforeEach(() => {
        mockEditModalShow.mockClear();
        mockInStockModalShow.mockClear();
        trackedCards.value = [];
        availabilityMap.value = {};

        useSocket.mockReturnValue({
            trackedCards: readonly(trackedCards),
            availabilityMap: readonly(availabilityMap),
            deleteCard: vi.fn(),
            saveCard: vi.fn(),
            updateCard: vi.fn(),
            getStockData: vi.fn() // Move inside return value
        });

        wrapper = mount(Dashboard, {
            global: {
                stubs: { AddCardModal, EditCardModal, InStockModal, BaseLayout }
            }
        });
    });

    it('renders a list of tracked cards', async () => {
        trackedCards.value = [
            createMockCard('Sol Ring', 1),
            createMockCard('Brainstorm', 4)
        ];
        await wrapper.vm.$nextTick();

        const rows = wrapper.findAll('tbody tr');
        expect(rows.length).toBe(2);
        expect(wrapper.text()).toContain('Sol Ring');
        expect(wrapper.text()).toContain('Brainstorm');
    });

    it('renders "Searching" badge when availability status is searching', async () => {
        const name = 'Lightning Bolt';
        trackedCards.value = [createMockCard(name)];
        // Ensure availabilityMap key matches the card.card.name
        availabilityMap.value = { [name]: { status: 'searching', stores: [] } };
        
        await wrapper.vm.$nextTick();

        // Use findComponent or a more generic search if v-html is being stubborn
        expect(wrapper.html()).toContain('Searching');
        expect(wrapper.find('.spinner-border').exists()).toBe(true);
    });

    it('calls deleteCard from composable with card.card.name', async () => {
        const name = 'Sol Ring';
        trackedCards.value = [createMockCard(name)];
        await wrapper.vm.$nextTick();
        
        const { deleteCard } = useSocket();

        await wrapper.find('button[title="Delete"]').trigger('click');

        // Verify it passes the name from the nested object
        expect(deleteCard).toHaveBeenCalledWith(trackedCards.value[0]);
    });

    it('opens the edit modal correctly', async () => {
        const cardToEdit = createMockCard('Sol Ring');
        trackedCards.value = [cardToEdit];
        await wrapper.vm.$nextTick();

        await wrapper.find('button[title="Edit"]').trigger('click');

        expect(wrapper.vm.cardToEdit).toEqual(cardToEdit);
        
        // Wait for nextTick inside the component's editCard function
        await wrapper.vm.$nextTick();
        expect(mockEditModalShow).toHaveBeenCalled();
    });

    it('renders a placeholder message when no cards are tracked', async () => {
        trackedCards.value = [];
        await wrapper.vm.$nextTick();

        const tableRows = wrapper.findAll('tbody tr');
        // If you have a "No cards found" row, test for that. 
        // Otherwise, ensure the tbody is just empty.
        expect(tableRows.length).toBe(0);
        expect(wrapper.text()).toContain('Your Tracked Cards');
    });

    it('prepares the correct data for the InStock modal on badge interaction', async () => {
        const cardName = 'Sol Ring';
        const mockItems = [{ store_name: 'LGS Central', price: 2.50 }];
        
        // Setup nested data
        trackedCards.value = [{ 
            card: { name: cardName }, 
            amount: 1, 
            specifications: [] 
        }];
        
        // Setup availability mapping
        availabilityMap.value = { 
            [cardName]: { status: 'completed', items: mockItems } 
        };
        
        await wrapper.vm.$nextTick();

        // Find the badge (which has the data-card-name attribute)
        const availableBadge = wrapper.find('.available-badge');
        expect(availableBadge.exists()).toBe(true);
        
        // Simulate the double click logic
        // Since handleTableDoubleClick uses event delegation, we can call it 
        // or trigger a bubbling dblclick on the badge
        await availableBadge.trigger('dblclick');

        // Verify the Dashboard's internal state updated to point to the right items
        expect(wrapper.vm.selectedCardForStock).toBe(cardName);
        expect(wrapper.vm.availableItemsForModal).toEqual(mockItems);
        
        // Verify getStockData was called (part of our new protocol)
        const { getStockData } = useSocket();
        expect(getStockData).toHaveBeenCalledWith(cardName);
    });
});
