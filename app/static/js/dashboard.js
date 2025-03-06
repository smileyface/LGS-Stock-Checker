// ✅ Define functions globally before WebSocket events fire
window.updateCardTable = function (data) {
    console.log("🔄 updateCardTable received data:", data);

    if (!data || !Array.isArray(data.tracked_cards)) {
        console.warn("⚠️ No valid tracked cards data received:", data);
        return;
    }

    let cardList = document.getElementById("cardTableBody");
    if (!cardList) {
        console.warn("⚠️ cardTableBody not found!");
        return;
    }

    let table = $("#cardTable").DataTable(); // ✅ Get existing DataTable instance
    table.clear(); // ✅ Clears old data

    // ✅ Remove the placeholder row before updating the table
    cardList.innerHTML = "";

    if (data.tracked_cards.length === 0) {
        console.warn("⚠️ No tracked cards available, keeping placeholder row.");
        cardList.innerHTML = `<tr><td colspan="5" class="text-center">No tracked cards found.</td></tr>`;
        table.draw();
        return;
    }

    data.tracked_cards.forEach((card, index) => {
        let rowData = [
            card.amount,
            card.card_name,
            card.set_code || "N/A",
            card.collector_id || "N/A",
            card.finish
        ];
        console.log(`🛠️ Adding row #${index + 1}:`, rowData); // ✅ Debug each row added
        table.row.add(rowData);
    });

    table.draw(); // ✅ Redraw DataTable
};



window.updateAvailabilityTable = function (data) {
    let tableBody = document.getElementById("availabilityTableBody");
    if (!tableBody) return;

    tableBody.innerHTML = "";

    if (data.error) {
        tableBody.innerHTML = `<tr><td colspan="4">${data.error}</td></tr>`;
    } else {
        data.availability.forEach((card, index) => {
            let storeDetails = "";
            Object.keys(card.stores).forEach(store => {
                let storeInfo = card.stores[store]
                    .map(s => `<li>${store}: $${s.price.toFixed(2)} - ${s.stock} in stock</li>`)
                    .join("");
                storeDetails += `<ul class="store-list" id="store-details-${index}" style="display: none;">${storeInfo}</ul>`;
            });

            let row = `
                <tr onclick="toggleStores(${index})">
                    <td>${card.card_name}</td>
                    <td>
                        <button class="btn btn-outline-primary btn-sm" onclick="toggleStores(${index}, event)">
                            Show Stores
                        </button>
                    </td>
                </tr>
                <tr>
                    <td colspan="2">${storeDetails}</td>
                </tr>
            `;
            tableBody.innerHTML += row;
        });
    }
};

document.addEventListener("DOMContentLoaded", function () {
    console.log("✅ Dashboard.js is loaded!");

    // ✅ Remove placeholder row before initializing DataTable
    let placeholderRow = document.querySelector("#cardTableBody .placeholder-row");
    if (placeholderRow) {
        placeholderRow.remove();
        console.log("🛠️ Placeholder row removed before DataTable initialization.");
    }

    setTimeout(() => {
        let columnCount = document.querySelectorAll("#cardTable thead tr th").length;
        let firstRowColumns = document.querySelectorAll("#cardTable tbody tr:first-child td").length;

        console.log(`🛠️ Debugging: Table has ${columnCount} headers and ${firstRowColumns} columns in first row.`);

        // ✅ Ensure DataTable only initializes when valid rows exist
        if (columnCount === firstRowColumns && firstRowColumns > 1) {
            if (!$.fn.DataTable.isDataTable("#cardTable")) {
                console.log("✅ Initializing DataTable...");
                $("#cardTable").DataTable({
                    paging: false,
                    searching: true,
                    ordering: true,
                    info: false
                });
            } else {
                console.warn("⚠️ DataTable is already initialized. Skipping reinitialization.");
            }
        } else {
            console.warn("⚠️ DataTable initialization skipped due to column mismatch.");
        }
    }, 500);
});

// ✅ Handle Card Search via WebSocket
let cardSearchInput = document.getElementById("cardSearch");
let searchResultsList = document.getElementById("searchResults");

cardSearchInput.addEventListener("input", function () {
    let query = cardSearchInput.value.trim();
    if (query.length < 3) {
        searchResultsList.innerHTML = "";
        return;
    }
    socket.emit("search_cards", { query: query });
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

function selectCard(card) {
    document.getElementById("cardSearch").value = card.name;
    document.getElementById("searchResults").innerHTML = "";
    document.getElementById("searchResults").setAttribute("data-selected-card", JSON.stringify(card));
}

// ✅ Handle Adding a Card
document.getElementById("saveCardButton").addEventListener("click", function () {
    let selectedCard = document.getElementById("searchResults").getAttribute("data-selected-card");
    if (!selectedCard) {
        alert("Please select a card before adding.");
        return;
    }

    let card = JSON.parse(selectedCard);
    let amount = parseInt(document.getElementById("amount").value) || 1;

    socket.emit("add_card", { card: card, amount: amount }); // ✅ Emit event via WebSocket
    $("#addCardModal").modal("hide"); // ✅ Close modal
});




