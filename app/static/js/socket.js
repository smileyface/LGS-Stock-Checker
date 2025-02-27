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
});

socket.on("connect_error", function (error) {
    console.error("❌ WebSocket Connection Error:", error);
});

socket.on("disconnect", function (reason) {
    console.warn("⚠️ Disconnected from WebSocket Server:", reason);
});

socket.on("server_log", function (data) {
    console.log(`📢 [SERVER LOG]: ${data.level}: ${data.message}`);
});

// Handle tracked cards update
socket.on("cards_data", function (data) {
    console.log("🛠️ Received cards_data:", data);

    waitForFunction("updateCardTable", () => {
        window.updateCardTable(data);
    });
});


// Handle availability updates
socket.on("card_availability_data", function (data) {
    if (!window.updateAvailabilityTable) {
        console.warn("⚠️ updateAvailabilityTable function not found!");
        return;
    }
    console.log("📡 Received availability update:", data);
    window.updateAvailabilityTable(data);
});


socket.on('availability_update', (data) => {
    console.log("🔔 Received availability update:", data);
});


// Function to trigger card availability request
function requestCardAvailability(selectedStores) {
    socket.emit("get_card_availability", { stores: selectedStores });
}
