

window.updateCardTable = function (data) {
    let table = $("#cardTable").DataTable();
    table.clear();

    if (!data || !Array.isArray(data.tracked_cards) || data.tracked_cards.length === 0) {
        console.warn("⚠️ No tracked cards available.");
        let $emptyRow = $(`
            <tr>
                <td colspan="6" class="text-center">No Cards Available</td>
            </tr>
        `);
        table.row.add($emptyRow);
        table.draw();
        return;
    }

    data.tracked_cards.forEach((card) => {
        let available = availabilityMap[card.card_name] === undefined
        ? "❌"
        : "✅";
        let $row = $(`
            <tr>
                <td>
                    <div class="action-buttons" data-card-name="${card.card_name}">
                        <button class="btn btn-sm btn-light edit-btn" title="Edit">✏️</button>
                        <button class="btn btn-sm btn-light delete-btn" title="Delete">❌</button>
                    </div>
                </td>
                <td class="amount-cell">${card.amount || "-"}</td>
                <td>${card.card_name || "-"}</td>
                <td>${card.set_code || "N/A"}</td>
                <td>${card.collector_id || "N/A"}</td>
                <td>${card.finish || "Non-Foil"}</td>
                <td>${available}<td>
            </tr>
        `);

        table.row.add($row);
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

        $("#cardTable tbody").on("click", ".edit-btn", function(){
            const row = $(this).closest("tr");
            const amountCell = row.find(".amount-cell");
            const currentAmount = amountCell.text().trim();

            // Replace cell content with input field
            amountCell.html(`<input type="number" class="form-control form-control-sm amount-input" value="${currentAmount}" min="1" style="max-width: 60px;" />`);

            // Change button to Save
            const btn = $(this);
            btn.removeClass("edit-btn").addClass("save-btn").html("💾");
        });

        $("#cardTable tbody").on("click", ".save-btn", function(){
            const row = $(this).closest("tr");
            const amountInput = row.find(".amount-input");
            const newAmount = amountInput.val();
            const cardName = row.find(".action-buttons").data("card-name");

            // Send update to backend
            socket.emit("update_card", {
                card: cardName,
                update_data: {
                    amount: parseInt(newAmount, 10)
                }
            });

            // Revert input to plain text
            row.find(".amount-cell").text(newAmount);

            // Change button back to Edit
            const btn = $(this);
            btn.removeClass("save-btn").addClass("edit-btn").html("✏️");

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




