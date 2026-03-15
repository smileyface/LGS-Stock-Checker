import { ref, readonly} from 'vue';
import { io, Socket } from 'socket.io-client';
import { 
    //Import Unions
    APIMessages,
    //Import Payloads
    UpdateCardRequestPayload,
    //Import Requests
    CardPreferenceSchema,
    UpdateCardRequest,
    CardsDataMessage,
    //Creation functions
    createGetCardsPayload,
    createUserSchema,

} from '../schema/server_types';

// --- State ---
const trackedCards = ref([]);
const isConnected = ref(false);

const handleIncomingCards = (message) => {
    // 1. Log it so you can see the data in the browser console
    console.log("📥 Received cards_data message:", message);

    // 2. Extract the cards from the payload
    // Based on your backend: payload = CardListPayload(cards=packed_cards)
    const cardList = message.payload.cards;

    if (!cardList || cardList.length === 0) {
        console.warn("⚠️ Received an empty card list.");
        return;
    }

    // 3. Map the data to your UI state

    trackedCards.value = message.payload.cards;
    console.log(`✅ Successfully loaded ${cardList.length} cards.`);
    
};

// --- Socket Connection ---
const socket: Socket = io({
    withCredentials: true,
    autoConnect: false
});

// --- Connection Logic ---
socket.on('connect', () => {
    const username = localStorage.getItem("username");
    isConnected.value = true;
    console.log("🔗 Connected!");
    const user = createGetCardsPayload(createUserSchema(username))
    emitMessage("get_cards", user);
});

socket.on('disconnect', () => {
    isConnected.value = false;
});

// --- Response Message Connecting ---
socket.on("cards_data", (data: unknown) => handleIncomingCards(data as CardsDataMessage));

// --- Emitter Functions (The "Clean" Way) ---

/**
 * Generic function to send card updates. 
 * TypeScript will now ensure 'data' matches our Pydantic backend.
 */
function sendCardUpdate(payload: UpdateCardRequestPayload) {
    const message: UpdateCardRequest = {
        name: "update_card",
        payload: payload
    };
    console.log("💾 Sending to Backend:", message);
    socket.emit('update_card', message);
}

// In your Auth Store or Login logic (NOT using emitMessage)
/**
async function login(credentials: LoginUserPayload) {
    const response = await fetch('/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials) // Still using your Pydantic-aligned structure!
    });

    if (response.ok) {
        // Now that we are logged in, we "Wake up" the socket
        //connectSocket(); 
        //TODO:Handle the socket connection 
    }
}*/

// Specific helpers that use the generic function above
function addCard(preference: CardPreferenceSchema) {
    sendCardUpdate({ command: 'add', update_data: preference });
}

function updateCard(preference: CardPreferenceSchema) {
    sendCardUpdate({ command: 'update', update_data: preference });
}

function deleteCard(preference: CardPreferenceSchema) {
    sendCardUpdate({ command: 'delete', update_data: preference });
}

// --- The Composable ---
export function useSocket() {
    if (!socket.connected) {
        socket.connect();
    }

    return {
        isConnected: readonly(isConnected),
        trackedCards: readonly(trackedCards),
        // Exporting our new clean functions
        addCard,
        updateCard,
        deleteCard
    };
}

/**
 * EMIT MESSAGE HELPER
 * * How the 'payload' type works:
 * 1. It takes the T (the message name, e.g., 'add_card').
 * 2. It looks at the APIMessages union and builds a temporary "Lookup Table".
 * 3. It maps every Message Name to its specific Payload type.
 * 4. It then picks the exact Payload type that matches the 'name' you provided.
 * * Why do it this way? 
 * This prevents TypeScript from getting confused when multiple messages share 
 * the same payload model. It's high-performance (zero runtime cost) and 
 * provides 100% accurate autocomplete based on the Python Pydantic models.
 * * If this is red: 
 * Check 'server_types.ts' to ensure the message in question actually has 
 * a 'payload' field defined in Python.
 */
function emitMessage<T extends APIMessages['name']>(
    name: T, 
    // This looks up the specific payload for the name provided
    payload: { 
    [K in APIMessages as K["name"]]: K extends { payload: infer P } ? P : never 
}[T]
) {
    if (!socket.connected) {
        console.error("🚫 Socket not connected!");
        return;
    }

    // We construct the full Pydantic-ready object here
    const message = { name, payload };

    console.log(`📡 Emitting to [${name}]:`, message);
    
    // We emit to the channel 'name', sending the whole 'message' object
    socket.emit(name, message);
}