function waitForFunction(fnName, callback) {
    let attempts = 10; // Maximum retries
    let interval = setInterval(() => {
        if (typeof window[fnName] === "function") {
            clearInterval(interval);
            callback();
        }
        attempts--;
        if (attempts === 0) {
            console.warn(`⚠️ Function ${fnName} not found after multiple attempts.`);
            clearInterval(interval);
        }
    }, 200);
}

let cardNameCache = [];
let availabilityMap = {};


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
    socket.emit("get_cards");
    socket.emit("get_card_availability");
    console.log("📡 Sent 'get_card_availability' event to backend");
    socket.emit("request_card_names"); // ✅ Ensure request happens only after connection
    console.log("📡 Sent 'request_card_names' event to backend");
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

// ✅ Wait for tables to be initialized before updating them
// ✅ Wait for DataTable and Data before Updating
socket.on("cards_data", function (data) {
    console.log("🛠️ Received cards_data:", data);

    function attemptUpdate() {
        if (!$.fn.DataTable.isDataTable("#cardTable")) {
            console.warn("⚠️ DataTable not initialized yet. Retrying...");
            setTimeout(attemptUpdate, 500);
            return;
        }

        if (!data.tracked_cards || data.tracked_cards.length === 0) {
            console.warn("⚠️ No tracked cards available.");
            return;
        }
        window.latestCardData = data; // Store for use when availability updates

        window.updateCardTable(data);
    }

    attemptUpdate(); // Start retry loop until ready
});

socket.on("card_availability_data", function (data) {
    console.log("📥 Received availability data:", data);
    availabilityMap = {}; // Reset for each batch
    data.forEach(entry => {
        // Use card name as key; you could also include set/collector filters if needed
        availabilityMap[entry.card_name] = entry.stores;
    });
    window.updateCardTable(window.latestCardData); // Re-render with updated info
});


socket.on("no_availability", function() {
    console.log("⚠️ No availability data received. Updating table.");
    window.updateAvailabilityTable(null);
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
    cardNameCache = data.card_names;
    console.log(`✅ Loaded ${data.card_names.length} card names for autocomplete.`);
});

// Function to trigger card availability request
function requestCardAvailability(selectedStores) {
    socket.emit("get_card_availability", { stores: selectedStores });
}
