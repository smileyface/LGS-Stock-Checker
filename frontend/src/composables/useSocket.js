import { ref, readonly } from 'vue';
import { io } from 'socket.io-client';

// --- State ---
// These are reactive and will be shared across any component using this composable.
const trackedCards = ref([]);
const availabilityMap = ref({});

// --- Socket Connection (Singleton pattern) ---
// Create the socket instance once. It will be shared across the application.
// The backend URL is explicitly provided. In a production environment,
// you might use an environment variable for this (e.g., import.meta.env.VITE_API_URL).
// For this setup, we'll hardcode it to the backend's exposed port.
const VITE_SOCKET_URL = import.meta.env.VITE_SOCKET_URL || 'http://localhost:5000';
const socket = io(VITE_SOCKET_URL, {
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

socket.on('cards_data', (data) => {
    console.log("🛠️ Received 'cards_data':", data);
    trackedCards.value = data.tracked_cards || [];
});

socket.on('availability_check_started', (data) => {
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

socket.on('card_availability_data', (data) => {
    if (!data || !data.card || !data.store) return;

    const cardName = data.card;
    const newItems = data.items || [];
    console.log(`📥 Received 'card_availability_data' for '${cardName}' from '${data.store}'. Found: ${newItems.length} items.`);

    // Ensure the entry for the card exists.
    if (!availabilityMap.value[cardName]) {
        availabilityMap.value[cardName] = { status: 'completed', items: [] };
    }

    // Get the existing items for this card.
    const existingItems = availabilityMap.value[cardName].items;

    // Create a Set of unique identifiers for the new items for efficient lookup.
    const newItemKeys = new Set(newItems.map(item => `${item.set_code}-${item.collector_number}-${item.finish}`));

    // 1. Filter out items from the same store that are no longer in stock.
    const updatedItems = existingItems.filter(item => {
        const itemKey = `${item.set_code}-${item.collector_number}-${item.finish}`;
        // Keep the item if it's from a different store, OR if it's from the same store and is still in the new list.
        return item.store_slug !== data.store || newItemKeys.has(itemKey);
    });

    // 2. Upsert (Update or Insert) new items.
    newItems.forEach(newItem => {
        const itemKey = `${newItem.set_code}-${newItem.collector_number}-${newItem.finish}`;
        const existingItemIndex = updatedItems.findIndex(
            item => item.store_slug === data.store && `${item.set_code}-${item.collector_number}-${item.finish}` === itemKey
        );

        if (existingItemIndex !== -1) {
            // Update price of existing item.
            updatedItems[existingItemIndex].price = newItem.price;
        } else {
            // Add new item, including the store slug for identification.
            updatedItems.push({ ...newItem, store_slug: data.store });
        }
    });

    availabilityMap.value[cardName].items = updatedItems;
    availabilityMap.value[cardName].status = 'completed';
});

socket.on('job_interrupted', (data) => {
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

socket.on('user_stores_data', (data) => {
    // This event is sent from the backend but was not being handled.
    // You can now use this data to update the UI, for example in a settings page.
    console.log("🏬 Received 'user_stores_data':", data.stores);
});

socket.on('stock_data', (data) => {
    if (!data || !data.card) return;
    const cardName = data.card;
    console.log(`📦 Received 'stock_data' for: ${cardName}`);
});

// --- Emitter Functions ---
function deleteCard(cardName) {
    console.log(`🗑️ Emitting 'delete_card' for: ${cardName}`);
    socket.emit('delete_card', { card: cardName });
}

function saveCard(cardData) {
    console.log("💾 Emitting 'add_card' with data:", cardData);
    socket.emit('add_card', cardData);
}

function updateCard(cardData) {
    console.log("🔄 Emitting 'update_card' with data:", cardData);
    socket.emit('update_card', cardData);
}

function getStockData(cardName) {
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
        saveCard,
        updateCard,
        getStockData
    };
}
