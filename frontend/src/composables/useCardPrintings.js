import { ref, computed, watch, onMounted, onUnmounted } from 'vue';
import { useSocket } from '@/composables/useSocket';
import {
    createGetPrintingsRequestPayload,
    createCardSchema
} from '@/schema/server_types';

/**
 * A Vue composable to manage fetching and deriving card printing data.
 * 
 * @param {import('vue').Ref<string>} cardNameRef - A ref holding the card name to fetch printings for.
 * @param {import('vue').Ref<string>} selectedSetRef - A ref holding the currently selected set code.
 * @param {import('vue').Ref<string>} selectedCollectorNumberRef - A ref holding the currently selected collector number.
 * @returns {object} An object containing reactive properties for printings and dropdown options.
 */
export function useCardPrintings(cardNameRef, selectedSetRef, selectedCollectorNumberRef) {
    const socketManager = useSocket();
    const printings = ref([]);

    // --- Data Fetching ---

    const fetchPrintings = (name) => {
        if (name && socketManager.socket) {
            console.log(`[useCardPrintings] 📡 Requesting printings for card: ${name}`);
            printings.value = []; // Clear old data before new fetch

    // 1. Build the leaf node (createCardSchema expects a raw string)
        const cardNode = createCardSchema(name);

        // 2. Build the payload (wrap in an object so it doesn't get shredded!)
        const payload = createGetPrintingsRequestPayload(cardNode);

        // 3. Emit with the hardcoded event string and the payload
        socketManager.socket.emitMessage('get_card_printings', payload);
        }
    };

    const handlePrintingsData = (data) => {
        // Only update if the received data is for the card we are currently interested in.
        if (data.card_name === cardNameRef.value) {
            console.log(`[useCardPrintings] 📩 Received printings data for: ${data.card_name}`, data.printings);
            printings.value = data.printings;
        }
    };

    // Watch the card name ref and fetch printings when it changes.
    watch(cardNameRef, (newName) => {
        fetchPrintings(newName);
    });

    // --- Lifecycle Hooks for Socket Listeners ---

    onMounted(() => {
        socketManager.socket?.on('card_printings_data', handlePrintingsData);
    });

    onUnmounted(() => {
        socketManager.socket?.off('card_printings_data', handlePrintingsData);
    });

    // --- Computed Properties for Dropdowns ---

    const setOptions = computed(() => {
        const sets = new Set(printings.value.map(p => p.set_code));
        return Array.from(sets);
    });

    const collectorNumberOptions = computed(() => {
        if (!selectedSetRef.value) return [];
        return printings.value
            .filter(p => p.set_code === selectedSetRef.value)
            .map(p => p.collector_number);
    });

    const finishOptions = computed(() => {
        if (!selectedSetRef.value || !selectedCollectorNumberRef.value) {
            return []; // Always return an array, not undefined!
        }

        const matchingPrinting = printings.value.find(
            (p) => p.set_code === selectedSetRef.value && p.collector_number === selectedCollectorNumberRef.value
        );

        // Ensure we return an array, even if finishes is missing
        return matchingPrinting?.finishes || []; 
    });

    return { printings, setOptions, collectorNumberOptions, finishOptions, fetchPrintings };
}
