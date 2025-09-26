/**
 * Renders the availability data as a series of Bootstrap badges.
 * @param {object | undefined} availability - The availability object for a card.
 * @returns {string} - HTML string of badges.
 */
function renderAvailability(availability) {
    if (!availability || availability.status === 'searching') {
        // If no data exists or the status is explicitly 'searching'.
        return `<span class="badge bg-info text-dark d-inline-flex align-items-center">
                    <span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>
                    Searching...</span>`;
    }
    if (!availability.stores || availability.stores.length === 0) {
        return '<span class="badge bg-secondary">Not Available</span>';
    }
    // Creates a green badge for each store the card is available in.
    return availability.stores.map(store => `<span class="badge bg-success me-1">${store}</span>`).join(' ');
}

/**
 * Clears and repopulates the main card DataTable with tracked cards and their availability.
 * @param {object} appState - The application state containing cards and availability.
 */
function updateCardTable(appState) {
    const table = $("#cardTable").DataTable();
    table.clear();

    if (!appState.trackedCards || appState.trackedCards.length === 0) {
        console.warn("updateCardTable called with no tracked cards. Clearing table.");
        table.draw();
        return;
    }

    const tableData = appState.trackedCards.map(card => {
        // For each card, look up its availability in the map using its name.
        const availability = appState.availabilityMap[card.card_name];
        const actionButtons = `
            <div class="action-buttons" data-card-name="${card.card_name}">
                <button class="btn btn-sm btn-light edit-btn" title="Edit">✏️</button>
                <button class="btn btn-sm btn-light delete-btn" title="Delete">❌</button>
            </div>`;

        // The order must match the columns in the HTML table
        return [
            actionButtons,
            `<div class="amount-cell">${card.amount || "-"}</div>`,
            card.card_name || "-",
            card.specifications?.[0]?.set_code || "N/A",
            card.specifications?.[0]?.collector_number || "N/A",
            card.specifications?.[0]?.finish || "Non-Foil",
            renderAvailability(availability)
        ];
    });

    table.rows.add(tableData).draw();
}

document.addEventListener("DOMContentLoaded", function () {
    console.log("✅ Dashboard.js is loaded!");

    function initializeCardTable() {
        if ($.fn.DataTable.isDataTable("#cardTable")) {
            console.log("✅ Card Table already initialized.");
            return;
        }

        console.log("✅ Initializing Card Table...");
        $("#cardTable").DataTable({
            paging: false,
            searching: true,
            ordering: true,
            info: false,
            // Ensure columns that contain HTML are not treated as plain text
            "columnDefs": [
                { "targets": [0, 1, 6], "type": "html", "orderable": false },
                { "targets": [0], "width": "80px" } // Give action buttons a fixed width
            ]
        });
    }

    function initializeAvailabilityTable() {
        if ($.fn.DataTable.isDataTable("#availabilityTable")) {
            console.log("✅ Availability Table already initialized.");
            return;
        }

        console.log("✅ Initializing Availability Table...");
        $("#availabilityTable").DataTable({
            paging: false,
            searching: true,
            ordering: true,
            info: false
        });
    }

    // --- Autocomplete Search ---
    let cardNameCache = []; // Local cache for autocomplete
    const cardSearchInput = document.getElementById("cardSearch");
    let searchResultsList = document.getElementById("searchResults");

    cardSearchInput.addEventListener("input", function () {
        let query = cardSearchInput.value.trim().toLowerCase();
        if (query.length < 2) {
            searchResultsList.innerHTML = "";
            return;
        }

        const filteredResults = appState.cardNameCache.filter(name => name.toLowerCase().includes(query)).slice(0, 10);
        searchResultsList.innerHTML = "";

        filteredResults.forEach(cardName => {
            let listItem = document.createElement("li");
            listItem.className = "list-group-item list-group-item-action";
            listItem.textContent = cardName;
            listItem.onclick = () => selectCard(cardName);
            searchResultsList.appendChild(listItem);
        });
    });

    // --- Initialize Tables ---
    initializeCardTable();
    initializeAvailabilityTable();

    // --- Listen for data updates from socket.js ---
    document.addEventListener('app:dataUpdated', function (e) {
        console.log("Received app:dataUpdated event", e.detail);
        cardNameCache = e.detail.cardNameCache || []; // Update local cache
        updateCardTable(e.detail);
    });

    // --- Event Delegation for Table Actions ---
    const tableBody = $("#cardTable tbody");

    // Handle Delete button clicks
    tableBody.on("click", ".delete-btn", function () {
        const row = $(this).closest("tr");
        const cardName = row.find(".action-buttons").data("card-name");
        if (cardName) {
            console.log(`🗑️ Deleting card: ${cardName}`);
            socket.emit("delete_card", { card: cardName });
            // The table will be redrawn when the server sends back the updated card list.
        }
    });

    // Handle entering edit mode
    tableBody.on("click", ".edit-btn", function () {
        const row = $(this).closest("tr");
        enterEditMode(row);
    });

    // Handle saving changes
    tableBody.on("click", ".save-btn", function () {
        const row = $(this).closest("tr");
        exitEditMode(row, true); // true = save changes
    });

    // Handle keyboard events for inline editing
    tableBody.on("keydown", ".amount-input", function (e) {
        const row = $(this).closest("tr");
        if (e.key === "Enter") {
            exitEditMode(row, true); // Save on Enter
        } else if (e.key === "Escape") {
            exitEditMode(row, false); // Cancel on Escape
        }
    });

    /** Enters edit mode for a specific table row. */
    function enterEditMode(row) {
        // If another row is already in edit mode, save it first.
        const currentlyEditing = tableBody.find(".save-btn").closest("tr");
        if (currentlyEditing.length > 0 && !currentlyEditing.is(row)) {
            exitEditMode(currentlyEditing, true);
        }

        const amountCell = row.find(".amount-cell");
        const currentAmount = amountCell.text().trim();
        amountCell.html(`<input type="number" class="form-control form-control-sm amount-input" value="${currentAmount}" min="1" style="max-width: 70px;" />`);
        amountCell.find("input").focus().select();

        const btn = row.find(".edit-btn");
        btn.removeClass("edit-btn").addClass("save-btn").html("💾").attr("title", "Save");
    }

    /** Exits edit mode for a row, optionally saving changes. */
    function exitEditMode(row, saveChanges) {
        const amountCell = row.find(".amount-cell");
        const amountInput = amountCell.find(".amount-input");
        if (amountInput.length === 0) return; // Not in edit mode

        const originalAmount = amountInput.attr("value");
        const newAmount = amountInput.val();
        const cardName = row.find(".action-buttons").data("card-name");

        if (saveChanges && newAmount !== originalAmount) {
            console.log(`💾 Saving new amount for ${cardName}: ${newAmount}`);
            socket.emit("update_card", {
                card: cardName,
                update_data: {
                    amount: parseInt(newAmount, 10)
                }
            });
            amountCell.text(newAmount);
        } else {
            // Revert to original value if cancelling or no change
            amountCell.text(originalAmount);
        }

        const btn = row.find(".save-btn");
        btn.removeClass("save-btn").addClass("edit-btn").html("✏️").attr("title", "Edit");
    }
});

function selectCard(cardName) {
    document.getElementById("cardSearch").value = cardName;
    document.getElementById("searchResults").innerHTML = "";
    document.getElementById("searchResults").setAttribute("data-selected-card", cardName);
}

// ✅ Handle Adding a Card
document.getElementById("saveCardButton").addEventListener("click", function () {
    let selectedCard = document.getElementById("searchResults").getAttribute("data-selected-card");
    if (!selectedCard) {
        alert("Please select a card before adding.");
        return;
    }

    let amount = parseInt(document.getElementById("amount")?.value || "1", 10);

    let cardSpecs = {
        set_code: document.getElementById("setCode")?.value || "Unknown",
        collector_id: document.getElementById("collectorNumber")?.value || "N/A",
        finish: document.querySelector('input[name="finish"]:checked')?.value || "Non-Foil"
    };

    if (!cardSpecs) {
        console.error("❌ card_specs is undefined!", { selectedCard, amount });
        return;
    }

    socket.emit("add_card", {
        card: selectedCard,
        amount: amount,
        card_specs: cardSpecs
    });

    console.log("📡 Sent 'add_card' event with:", { selectedCard, amount, cardSpecs });

    $("#addCardModal").modal("hide");

    document.getElementById("cardSearch").value = "";
    document.getElementById("amount").value = "1"; // Reset to default
});
