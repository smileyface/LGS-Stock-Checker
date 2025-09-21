// --- State Management ---
// Encapsulate state in a single object to avoid polluting the global scope.
const appState = {
    cardNameCache: [],
    availabilityMap: {},
    trackedCards: [],
};

// Debounce timer for UI updates to prevent rapid re-renders.
let uiUpdateTimeout = null;

/**
 * Dispatches a debounced custom event to trigger a UI update.
 * This prevents the UI from re-rendering too frequently when data arrives in bursts.
 */
function dispatchUiUpdate() {
    clearTimeout(uiUpdateTimeout);
    uiUpdateTimeout = setTimeout(() => {
        console.log("🚀 Dispatching debounced UI update.");
        const event = new CustomEvent('app:dataUpdated', { detail: appState });
        document.dispatchEvent(event);
    }, 200); // Wait 200ms after the last event to update the UI.
}

const socket = io({ withCredentials: true });

// Debugging for connection status
socket.on("connect", function () {
    console.log("🔗 Connected to WebSocket Server!");
    // Chain requests to ensure a predictable data flow and reduce re-renders.
    // First, get the list of cards and the names for autocomplete.
    socket.emit("get_cards");
    socket.emit("request_card_names");
});

//Error connecting to the server
socket.on("connect_error", function (error) {
    console.error("❌ WebSocket Connection Error:", error);
});

//Disconnect from server
socket.on("disconnect", function (reason) {
    console.warn("⚠️ Disconnected from WebSocket Server:", reason);
});

// Send log info to the console
socket.on("server_log", function (data) {
    console.log(`📢 [SERVER LOG]: ${data.level}: ${data.message}`);
});

socket.on("cards_data", function (data) {
    console.log("🛠️ Received cards_data:", data);

    // Update the tracked cards list, defaulting to an empty array if none are provided.
    appState.trackedCards = data?.tracked_cards || [];
    if (appState.trackedCards.length === 0) {
        console.warn("⚠️ No tracked cards available. Table will be cleared.");
    }

    // Trigger a UI update immediately to render the card list.
    // Availability will be filled in as it arrives.
    dispatchUiUpdate();

    // Now that we have the latest card list, request their availability.
    socket.emit("get_card_availability");
    console.log("📡 Sent 'get_card_availability' event to backend");
});

socket.on("card_availability_data", function (data) {
    console.log("📥 Received availability data:", data);

    // The backend sends incremental updates for each card/store combination.
    // We need to build the availability map piece by piece.
    if (data && data.card && data.store) {
        const cardName = data.card;
        const storeName = data.store;
        const isAvailable = data.items && data.items.length > 0;

        // Ensure the card has an entry in the map.
        if (!appState.availabilityMap[cardName]) {
            appState.availabilityMap[cardName] = [];
        }

        const storeIndex = appState.availabilityMap[cardName].indexOf(storeName);

        if (isAvailable && storeIndex === -1) {
            // Add the store to the list if it's available and not already present.
            appState.availabilityMap[cardName].push(storeName);
        } else if (!isAvailable && storeIndex !== -1) {
            // Remove the store if it's no longer available.
            appState.availabilityMap[cardName].splice(storeIndex, 1);
        }
    } else {
        console.warn("⚠️ Received malformed availability data:", data);
        return; // Do not proceed with malformed data.
    }

    // Trigger a debounced UI update to show the new availability status.
    dispatchUiUpdate();
});

socket.on("card_names_response", function (data) {
    if (!data || !Array.isArray(data.card_names)) {
        console.warn("⚠️ Invalid card names received:", data);
        return;
    }
    appState.cardNameCache = data.card_names;
    console.log(`✅ Loaded ${data.card_names.length} card names for autocomplete.`);
});
