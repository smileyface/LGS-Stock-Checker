import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { mount } from '@vue/test-utils';
import EditCardModal from '../src/components/EditCardModal.vue';
import { ref } from 'vue';

// --- Mocks ---

// Mock Bootstrap's Modal
const mockModalInstance = {
    show: vi.fn(),
    hide: vi.fn(),
};
vi.mock('bootstrap', () => ({
    Modal: vi.fn(() => mockModalInstance),
}));

// Mock the useCardPrintings composable
vi.mock('../src/composables/useCardPrintings', () => ({
    useCardPrintings: vi.fn(() => ({
        setOptions: ref(['C21', 'MOC']), // Provide stable options
        collectorNumberOptions: ref(['333']),
        finishOptions: ref(['non-foil', 'foil']),
        fetchPrintings: vi.fn(),
    })),
}));


describe('EditCardModal.vue', () => {
    const cardProp = {
        card_name: 'Sol Ring',
        amount: 1,
        specifications: [{
            set_code: 'C21',
            collector_number: '333',
            finish: 'non-foil'
        }]
    };

    beforeEach(() => {
        // Reset mocks before each test to ensure isolation
        vi.clearAllMocks();
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    it('renders the modal with data from the cardToEdit prop', async () => {
        const wrapper = mount(EditCardModal, {
            props: { cardToEdit: cardProp }
        });

        wrapper.vm.show();

        // Wait for Vue to update the DOM after the state change from the event
        await wrapper.vm.$nextTick();

        expect(wrapper.find('h5.modal-title').text()).toContain('Edit: Sol Ring');
        expect(wrapper.find('#editCardAmount').element.value).toBe('1');
        expect(wrapper.find('#edit_set_code').element.value).toBe('C21');
        expect(wrapper.find('#edit_collector_number').element.value).toBe('333');
        expect(wrapper.find('#edit_finish').element.value).toBe('non-foil');
    });

    it('handles cards with no initial specifications', async () => {
        const cardWithoutSpecs = {
            card_name: 'Brainstorm',
            amount: 4,
            specifications: [] // Empty array
        };
        const wrapper = mount(EditCardModal, {
            props: { cardToEdit: cardWithoutSpecs }
        });

        wrapper.vm.show();

        // Wait for Vue to update the DOM
        await wrapper.vm.$nextTick();

        // Assert that default values are provided for the form
        expect(wrapper.find('#edit_set_code').element.value).toBe('');
        expect(wrapper.find('#edit_collector_number').element.value).toBe('');
        expect(wrapper.find('#edit_finish').element.value).toBe('');
    });

    it("emits 'update-card' with the correct payload on submission", async () => {
        // Spy on the hide method to prevent it from being called and potentially unmounting the component
        const hideSpy = vi.spyOn(mockModalInstance, 'hide');

        const wrapper = mount(EditCardModal, {
            props: { cardToEdit: cardProp }
        });

        // Show the modal to populate the form
        wrapper.vm.show();

        // Wait for Vue to update the DOM
        await wrapper.vm.$nextTick();

        // Simulate user edits
        await wrapper.find('#editCardAmount').setValue(4);
        await wrapper.find('#edit_set_code').setValue('MOC');
        await wrapper.find('#edit_collector_number').setValue('333'); // Need to re-select to enable finish
        await wrapper.find('#edit_finish').setValue('foil');

        // Trigger submission by clicking the save button
        await wrapper.find('button.btn-primary').trigger('click');

        // Assert that the event was emitted with the correct data
        expect(wrapper.emitted()).toHaveProperty('update-card');
        const emittedPayload = wrapper.emitted('update-card')[0][0];

        expect(emittedPayload).toEqual({
            card: 'Sol Ring', // The original card name
            update_data: {
                amount: 4,
                specifications: [{
                    set_code: 'MOC',
                    collector_number: '333',
                    finish: 'foil'
                }]
            }
        });

        // Assert that the modal was hidden
        expect(hideSpy).toHaveBeenCalled();
    });

    it('exposes a show method that calls the modal instance show', () => {
        const wrapper = mount(EditCardModal, {
            props: { cardToEdit: cardProp }
        });

        // Call the exposed method
        wrapper.vm.show();

        expect(mockModalInstance.show).toHaveBeenCalled();
    });
});
