window.updateCardTable = function (data) {
    let table = $("#cardTable").DataTable();
    table.clear();

    if (!data || !Array.isArray(data.tracked_cards) || data.tracked_cards.length === 0) {
        console.warn("⚠️ No tracked cards available.");
        table.row.add([
            '<td colspan="5" class="text-center">No Cards Available</td>',
            "", "", "", ""
        ]); // Empty strings prevent column mismatch
        table.draw();
        return;
    }

    data.tracked_cards.forEach((card) => {
        let rowData = [
            `
            <div class="action-buttons" data-card-name="${card.card_name}">
                <button class="btn btn-sm btn-light edit-btn" title="Edit">✏️</button>
                <button class="btn btn-sm btn-light delete-btn" title="Delete">❌</button>
            </div>
            `,
            card.amount || "-",
            card.card_name || "-",
            card.set_code || "N/A",
            card.collector_id || "N/A",
            card.finish || "Non-Foil"
        ];

        if (rowData.length === 6) {
            table.row.add(rowData);
        } else {
            console.error("❌ Invalid row data (incorrect column count):", rowData);
        }
    });

    table.draw();
};


window.updateAvailabilityTable = function (data) {
    let table = $("#availabilityTable").DataTable();
    table.clear();

    if (!data || !Array.isArray(data.availability) || data.availability.length === 0) {
        console.warn("⚠️ No availability data available.");
        table.row.add(["No Availability", "", ""]); // ✅ Matches exactly 3 columns
        table.draw();
        return;
    }

    data.availability.forEach((card, index) => {
        let storeDetails = "";
        Object.keys(card.stores).forEach(store => {
            let storeInfo = card.stores[store]
                .map(s => `<li>${store}: $${s.price.toFixed(2)} - ${s.stock} in stock</li>`)
                .join("");
            storeDetails += `<ul class="store-list" id="store-details-${index}" style="display: none;">${storeInfo}</ul>`;
        });

        let row = [
            card.card_name || "-",
            `<button class="btn btn-outline-primary btn-sm" onclick="toggleStores(${index}, event)">Show Stores</button>${storeDetails}`
        ];

        if (row.length === 2) {
            table.row.add(row);
        } else {
            console.error("❌ Invalid row data (incorrect column count):", row);
        }
    });

    table.draw();
};


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
            info: false
        });
        $("#cardTable tbody").on("click", ".delete-btn", function () {
            const row = $(this).closest("tr");
            const cardName = row.find(".action-buttons").data("card-name");

            if (!cardName) {
                console.error("❌ Could not find card name to delete.");
                return;
            }

            console.log(`🗑️ Deleting card: ${cardName}`);
            socket.emit("delete_card", { card: cardName });

            // Optional: remove the row from the table immediately
            $("#cardTable").DataTable().row(row).remove().draw();
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

    initializeCardTable();
    initializeAvailabilityTable();
});




document.addEventListener("DOMContentLoaded", function () {
    let cardSearchInput = document.getElementById("cardSearch");
    let searchResultsList = document.getElementById("searchResults");

    cardSearchInput.addEventListener("input", function () {
        let query = cardSearchInput.value.trim().toLowerCase();
        if (query.length < 2) {
            searchResultsList.innerHTML = "";
            return;
        }

        // ✅ Filter card names from cache for autocomplete
        let filteredResults = cardNameCache.filter(name => name.toLowerCase().includes(query)).slice(0, 10);
        searchResultsList.innerHTML = "";

        filteredResults.forEach(cardName => {
            let listItem = document.createElement("li");
            listItem.className = "list-group-item list-group-item-action";
            listItem.textContent = cardName;
            listItem.onclick = () => selectCard(cardName);
            searchResultsList.appendChild(listItem);
        });
    });
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

    console.log("📡 Sent 'add_card' event with:", { selectedCard, amount, card_specs });

    $("#addCardModal").modal("hide");
});




