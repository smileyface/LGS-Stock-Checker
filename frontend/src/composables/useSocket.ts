import { ref, readonly, Ref } from 'vue';
import { io, Socket } from 'socket.io-client';
// 1. Import your new types
import type { 
    UpdateCardRequest, 
    LoginUserPayload,
    CardPreferenceSchema,
    UpdateCardRequestPayload,
    AppMessage
} from '../types/messaging';

// --- State ---
const trackedCards = ref([]); // We'll type this once we finish the "Receive" schemas
const isConnected = ref(false);

// --- Socket Connection ---
const socket: Socket = io({
    withCredentials: true,
    autoConnect: false
});

// --- Connection Logic ---
socket.on('connect', () => {
    isConnected.value = true;
    console.log("🔗 Connected!");
    emitMessage("get_cards", {})
});

socket.on('disconnect', () => {
    isConnected.value = false;
});

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
}

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
 * Generic Emitter
 * T extends the 'name' field of any message in our AppMessage union.
 */
function emitMessage<T extends AppMessage['name']>(
    name: T, 
    // This looks up the specific payload for the name provided
    payload: Extract<AppMessage, { name: T }>['payload']
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