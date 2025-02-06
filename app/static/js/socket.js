var socket = io.connect(window.location.origin);

socket.on("inventory_update", function (data) {
    console.log("🔄 Received inventory update:", data.card);

    if (data.items.length === 0) {
        console.log(`Skipping update: No items for ${data.card} at ${data.store}.`);
        return;
    }

    let table = document.getElementById("inventoryTable");
    if (!table) return; // ✅ Prevents running on the wrong page

    let tbody = table.getElementsByTagName("tbody")[0];

    // Find and remove old entries for this card/store
    [...tbody.getElementsByTagName("tr")].forEach(row => {
        if (row.cells[0].innerText === data.card && row.cells[1].innerText === data.store) {
            row.remove();
        }
    });

    // Insert new listings
    data.items.forEach(item => {
        let newRow = tbody.insertRow();
        newRow.insertCell(0).innerText = data.card;
        newRow.insertCell(1).innerText = data.store;
        newRow.insertCell(2).innerText = item.condition;
        newRow.insertCell(3).innerText = item.finish;
        newRow.insertCell(4).innerText = item.set;
        newRow.insertCell(5).innerText = item.stock;
        newRow.insertCell(6).innerText = item.price;
    });
});
