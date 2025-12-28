import { ref, readonly, Ref } from 'vue';
import { io, Socket } from 'socket.io-client';
import { createCardPreferenceSchema } from '../schema/server_types';
import type {
    UserTrackedCardSchema,
    CardPreferenceSchema,
    UpdateCardRequestPayload,
    CardSpecificationSchema,
    AvailabilityResultPayload,
    AddCardMessage
} from '../schema/server_types'; // Adjust path if needed

// --- Wire Types (To handle current backend response format) ---
// This matches what backend/managers/user_manager/user_cards.py currently emits.
interface WireUserTrackedCard {
    card_name: string;
    amount: number;
    specifications: CardSpecificationSchema[];
}

interface WireCardsDataPayload {
    username: string;
    tracked_cards: WireUserTrackedCard[];
}

// --- Local Types for State ---
interface AvailabilityStatus {
    status: 'searching' | 'completed' | 'stalled';
    items: any[];
}

// --- State ---
const trackedCards: Ref<UserTrackedCardSchema[]> = ref([]);
const availabilityMap: Ref<Record<string, AvailabilityStatus>> = ref({});
const isConnected = ref(false);

// --- Socket Connection ---
// const VITE_SOCKET_URL = import.meta.env.VITE_SOCKET_URL || 'http://localhost:5000';
const socket: Socket = io({
    withCredentials: true,
    autoConnect: false
});

// --- Event Handlers ---
socket.on('connect', () => {
    isConnected.value = true;
    console.log("🔗 Connected to WebSocket Server!");
    socket.emit("get_cards");
    socket.emit("get_card_availability");
});

socket.on('disconnect', () => {
    isConnected.value = false;
    console.log("🔌 Disconnected from WebSocket Server");
});

socket.on('cards_data', (data: WireCardsDataPayload) => {
    console.log("🛠️ Received 'cards_data' (Wire Format):", data);

    // TRANSFORM: Convert flat wire format to strictly typed Schema format
    // This allows the rest of the frontend to use 'card.name' consistently.
    const transformedCards: UserTrackedCardSchema[] = (data.tracked_cards || []).map(wireCard => ({
        card: { name: wireCard.card_name },
        amount: wireCard.amount,
        specifications: wireCard.specifications
    }));

    trackedCards.value = transformedCards;
});

socket.on('availability_check_started', (data: { card: string }) => {
    if (!data?.card) return;
    const cardName = data.card;
    const existingEntry = availabilityMap.value[cardName] || { items: [] };
    availabilityMap.value[cardName] = { ...existingEntry, status: 'searching' };
});

socket.on('card_availability_data', (data: { card: string, store_slug: string, items: any[] }) => {
    if (!data?.card || !data.store_slug) return;
    const cardName = data.card;
    const newItems = data.items || [];

    if (!availabilityMap.value[cardName]) {
        availabilityMap.value[cardName] = { status: 'completed', items: [] };
    }

    const existingItems = availabilityMap.value[cardName].items || [];
    // Replace items for this specific store
    const otherStoreItems = existingItems.filter(item => item.store_slug !== data.store_slug);
    const itemsForCurrentStore = newItems.map(item => ({ ...item, store_slug: data.store_slug }));

    availabilityMap.value[cardName].items = [...otherStoreItems, ...itemsForCurrentStore];
    availabilityMap.value[cardName].status = 'completed';
});

socket.on('stock_data', (data: { card_name: string, items: any[] }) => {
    // Handle aggregate stock data if needed
    console.log(`📦 Received stock data for ${data.card_name}`);
});

// --- Emitter Functions ---

function addCard(cardData: AddCardMessage) {
    // Backend expects strict Pydantic structure now
    console.log("💾 Emitting 'add_card' with data:", cardData);
    socket.emit('add_card', cardData);
}

function updateCard(cardData: CardPreferenceSchema) {
    console.log("🔄 Emitting 'update_card' with data:", cardData);
    socket.emit('update_card', cardData);
}

function deleteCard(cardName: string) {
    // We construct the schema subset required for deletion
    // The backend looks for data['card']['name']
    const payload = {
        card: { name: cardName }
    };
    console.log("❌ Emitting 'delete_card' with data:", payload);
    socket.emit('delete_card', payload);
}

function getStockData(cardName: string) {
    socket.emit('stock_data_request', { card_name: cardName });
}

export function useSocket() {
    if (!socket.connected) {
        socket.connect();
    }

    return {
        socket,
        isConnected: readonly(isConnected),
        trackedCards: readonly(trackedCards),
        availabilityMap: readonly(availabilityMap),
        deleteCard,
        addCard,
        updateCard,
        getStockData
    };
}