import { ref, readonly, Ref } from 'vue';
import { io, Socket } from 'socket.io-client';
import type {
    UserTrackedCardListSchema,
    UserTrackedCardSchema,
    UpdateCardRequestPayload,
} from '../schema/server_types';

/**
 * Local type definitions for data structures not covered by the generated server types.
 */
interface AvailabilityStatus {
    status: 'searching' | 'completed' | 'stalled';
    items: any[]; // Consider creating a specific type for these items if the structure is known
}

interface CardAvailabilityData {
    card: string;
    store_slug: string;
    items: any[];
}

// --- State ---
// These are reactive and will be shared across any component using this composable.
const trackedCards: Ref<UserTrackedCardSchema[]> = ref([]);
const availabilityMap: Ref<Record<string, AvailabilityStatus>> = ref({});

// --- Socket Connection (Singleton pattern) ---
// Create the socket instance once. It will be shared across the application.
// The backend URL is explicitly provided. In a production environment,
// you might use an environment variable for this (e.g., import.meta.env.VITE_API_URL).
// For this setup, we'll hardcode it to the backend's exposed port.
// const VITE_SOCKET_URL = import.meta.env.VITE_SOCKET_URL || 'http://localhost:5000';
const socket: Socket = io({
    withCredentials: true, 
    autoConnect: false // We will connect manually when the composable is first used.
});

// --- Event Handlers ---
socket.on('connect', () => {
    console.log("🔗 Connected to WebSocket Server!");
    // Now that we are connected, request initial data.
    console.log("📡 Emitting 'get_cards' to fetch user's tracked cards.");
    socket.emit("get_cards");
    console.log("📡 Emitting 'get_card_availability' to fetch initial availability.");
    socket.emit("get_card_availability");
});

socket.on('cards_data', (data: UserTrackedCardListSchema) => {
    console.log("🛠️ Received 'cards_data':", data);
    trackedCards.value = data.tracked_cards || [];
});

socket.on('availability_check_started', (data: { card: string }) => {
    if (!data || !data.card) return;
    const cardName = data.card;
    console.log(`⏳ Received 'availability_check_started' for: ${cardName}`);
    // Ensure the base object exists with an items array before setting status.
    const existingEntry = availabilityMap.value[cardName] || { items: [] };
    // Set the status to 'searching' to trigger the spinner in the UI, preserving existing items if any.
    availabilityMap.value[cardName] = {
        ...existingEntry,
        status: 'searching'
    };
});

socket.on('card_availability_data', (data: CardAvailabilityData) => {
    if (!data || !data.card || !data.store_slug) return;

    const cardName = data.card;
    const newItems = data.items || [];
    console.log(`📥 Received 'card_availability_data' for '${cardName}' from '${data.store_slug}'. Found: ${newItems.length} items.`);

    // Ensure the entry for the card exists.
    if (!availabilityMap.value[cardName]) {
        availabilityMap.value[cardName] = { status: 'completed', items: [] };
    }

    // Get the existing items for this card, or an empty array if none.
    const existingItems = availabilityMap.value[cardName]?.items || [];

    // 1. Filter out all items from the store that sent the update.
    const otherStoreItems = existingItems.filter(
        item => item.store_slug !== data.store_slug
    );

    // 2. Add the new items, ensuring they have the store slug for future identification.
    const itemsForCurrentStore = newItems.map(item => ({ ...item, store_slug: data.store_slug }));

    // 3. Combine the lists.
    const updatedItems = [...otherStoreItems, ...itemsForCurrentStore];

    availabilityMap.value[cardName].items = updatedItems;
    availabilityMap.value[cardName].status = 'completed';
});

socket.on('job_interrupted', (data: { card: string }) => {
    if (!data || !data.card) return;
    const cardName = data.card;
    console.warn(`🚦 Received 'job_interrupted' for: ${cardName}.`);

    // If we have an entry for this card, mark its status as stalled.
    if (availabilityMap.value[cardName]) {
        availabilityMap.value[cardName] = {
            ...availabilityMap.value[cardName],
            status: 'stalled' // A new status to indicate interruption.
        };
    }
});

socket.on('user_stores_data', (data: { stores: string[] }) => {
    // This event is sent from the backend but was not being handled.
    // You can now use this data to update the UI, for example in a settings page.
    console.log("🏬 Received 'user_stores_data':", data.stores);
});

socket.on('stock_data', (data: { card: string }) => {
    if (!data || !data.card) return;
    const cardName = data.card;
    console.log(`📦 Received 'stock_data' for: ${cardName}`);
});

// --- Emitter Functions ---
function deleteCard(cardData: UpdateCardRequestPayload) {
    console.log("💾 Emitting 'add_card' with data:", cardData);
    cardData.command = "delete";
    socket.emit('delete_card', cardData);
}

function addCard(cardData: UpdateCardRequestPayload) {
    console.log("💾 Emitting 'add_card' with data:", cardData);
    cardData.command = "add";
    socket.emit('add_card', cardData);
}

function updateCard(cardData: UpdateCardRequestPayload) {
    console.log("🔄 Emitting 'update_card' with data:", cardData);
    cardData.command = "update";
    socket.emit('update_card', cardData);
}

function getStockData(cardName: string) {
    console.log(`🔍 Emitting 'stock_data_request' for: ${cardName}`);
    socket.emit('stock_data_request', { card_name: cardName });
}

/**
 * The main composable function.
 */
export function useSocket() {
    if (!socket.connected) {
        socket.connect();
    }

    return {
        socket, // Expose the raw socket instance for custom event handling
        trackedCards: readonly(trackedCards),
        availabilityMap: readonly(availabilityMap),
        deleteCard,
        addCard,
        updateCard,
        getStockData
    };
}

// Export for testing purposes only
export { socket };
export const _internal = {
    trackedCards,
    availabilityMap,
};
