window.updateCardTable = function (data) {
    let table = $("#cardTable").DataTable();
    table.clear();

    if (!data || !Array.isArray(data.tracked_cards) || data.tracked_cards.length === 0) {
        console.warn("⚠️ No tracked cards available, inserting placeholder row.");
        table.row.add(["-", "No Cards", "-", "-", "-"]); // ✅ Matches exactly 5 columns
        table.draw();
        return;
    }

    data.tracked_cards.forEach((card) => {
        let rowData = [
            card.amount || "-",
            card.card_name || "-",
            card.set_code || "N/A",
            card.collector_id || "N/A",
            card.finish || "Non-Foil"
        ];

        if (rowData.length === 5) {
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
        table.row.add(["No Availability", ""]); // ✅ Matches exactly 2 columns
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

    // ✅ Ensure DataTables initializes only once
    if (!$.fn.DataTable.isDataTable("#cardTable")) {
        console.log("✅ Initializing Card Table...");
        $("#cardTable").DataTable({
            paging: false,
            searching: true,
            ordering: true,
            info: false
        });
    }

    if (!$.fn.DataTable.isDataTable("#availabilityTable")) {
        console.log("✅ Initializing Availability Table...");
        $("#availabilityTable").DataTable({
            paging: false,
            searching: true,
            ordering: true,
            info: false
        });
    }
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

    socket.emit("add_card", {
        card: selectedCard,
        amount: amount,
        card_specs: cardSpecs
    });

    console.log("📡 Sent 'add_card' event with:", { selectedCard, amount, card_specs });

    $("#addCardModal").modal("hide"); // ✅ Close modal
});




