import { ref, readonly } from 'vue';
import { io } from 'socket.io-client';

// --- State ---
// These are reactive and will be shared across any component using this composable.
const trackedCards = ref([]);
const availabilityMap = ref({});

// --- Socket Connection (Singleton pattern) ---
// Create the socket instance once. It will be shared across the application.
const socket = io({
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
    // Set the status to 'searching' to trigger the spinner in the UI.
    availabilityMap.value[cardName] = { status: 'searching', stores: [] };
});

socket.on('card_availability_data', (data) => {
    if (!data || !data.card || !data.store) return;

    const cardName = data.card;
    const storeName = data.store;
    const isAvailable = data.items && data.items.length > 0;
    console.log(`📥 Received 'card_availability_data' for '${cardName}' from '${storeName}'. Available: ${isAvailable}`);

    if (!availabilityMap.value[cardName]) {
        availabilityMap.value[cardName] = { status: 'searching', stores: [] };
    }

    availabilityMap.value[cardName].status = 'completed';

    const storeIndex = availabilityMap.value[cardName].stores.indexOf(storeName);
    if (isAvailable && storeIndex === -1) {
        availabilityMap.value[cardName].stores.push(storeName);
    } else if (!isAvailable && storeIndex !== -1) {
        availabilityMap.value[cardName].stores.splice(storeIndex, 1);
    }
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

/**
 * The main composable function.
 */
export function useSocket() {
    if (!socket.connected) {
        socket.connect();
    }

    return {
        trackedCards: readonly(trackedCards),
        availabilityMap: readonly(availabilityMap),
        deleteCard,
        saveCard,
        updateCard,
    };
}