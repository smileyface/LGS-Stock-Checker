/**
 * Waits for a condition to be true before executing a callback.
 * @param {() => boolean} condition - A function that returns true when the condition is met.
 * @param {() => void} callback - The function to execute once the condition is met.
 */
function pollUntil(condition, callback) {
    let attempts = 20; // Maximum retries (e.g., 20 * 250ms = 5 seconds)
    let interval = setInterval(() => {
        if (condition()) {
            clearInterval(interval);
            callback();
        } else if (--attempts === 0) {
            console.warn(`⚠️ Condition not met after multiple attempts. Aborting.`);
            clearInterval(interval);
        }
    }, 250);
}

// --- State Management ---
// Encapsulate state in a single object to avoid polluting the global scope.
const appState = {
    cardNameCache: [],
    availabilityMap: {},
    latestCardData: null,
};

var socket = io.connect(window.location.origin, {
    transports: ["websocket", "polling"], // Ensure WebSockets are prioritized
    reconnection: true, // Enable automatic reconnection
    reconnectionAttempts: 10, // Retry up to 10 times
    reconnectionDelay: 5000, // Wait 5 seconds between retries
    timeout: 20000 // 20 seconds timeout before failing
});

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

    if (!data || !data.tracked_cards || data.tracked_cards.length === 0) {
        console.warn("⚠️ No tracked cards available in received data.");
        return;
    }
    appState.latestCardData = data; // Store state locally

    // Now that we have the cards, request their availability.
    // This prevents the table from rendering twice in quick succession on initial load.
    socket.emit("get_card_availability");
    console.log("📡 Sent 'get_card_availability' event to backend");
});

socket.on("card_availability_data", function (data) {
    console.log("📥 Received availability data:", data);
    const newAvailabilityMap = {};
    data.forEach(entry => {
        // Use card name as key; you could also include set/collector filters if needed
        newAvailabilityMap[entry.card_name] = entry.stores;
    });
    appState.availabilityMap = newAvailabilityMap;

    // This is now the single point of truth for rendering the table with all data.
    pollUntil(
        () => $.fn.DataTable.isDataTable("#cardTable"),
        () => window.updateCardTable(appState.latestCardData, appState.availabilityMap)
    );
});

// ✅ Receive Search Results and Populate List
socket.on("search_results", function (data) {
    searchResultsList.innerHTML = "";
    data.forEach(card => {
        let listItem = document.createElement("li");
        listItem.className = "list-group-item list-group-item-action";
        listItem.innerHTML = `${card.name} <small>(${card.set_code})</small>`;
        listItem.onclick = () => selectCard(card);
        searchResultsList.appendChild(listItem);
    });
});

socket.on("card_names_response", function (data) {
    if (!data || !Array.isArray(data.card_names)) {
        console.warn("⚠️ Invalid card names received:", data);
        return;
    }
    appState.cardNameCache = data.card_names;
    console.log(`✅ Loaded ${data.card_names.length} card names for autocomplete.`);
});

// Function to trigger card availability request
function requestCardAvailability(selectedStores) {
    socket.emit("get_card_availability", { stores: selectedStores });
}
