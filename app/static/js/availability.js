document.addEventListener("DOMContentLoaded", function () {
    let refreshButton = document.getElementById("refreshAvailability");
    let spinner = document.getElementById("refreshSpinner");
    let lastUpdated = document.getElementById("lastUpdated");

    if (!refreshButton) return; // ✅ Prevents running on the wrong page

    refreshButton.addEventListener("click", function () {
        console.log("Refresh button clicked!");
        refreshButton.disabled = true;
        spinner.style.display = "inline-block";

        fetch(refreshButton.dataset.url, {
            method: "POST",
            headers: { "Content-Type": "application/json" }
        })
            .then(response => response.json())
            .then(data => {
                console.log("Availability refresh triggered:", data);
                lastUpdated.innerText = `Last Updated: ${new Date().toLocaleString()}`;
            })
            .catch(error => console.error("Fetch error:", error))
            .finally(() => {
                spinner.style.display = "none";
                refreshButton.disabled = false;
            });
    });

    document.querySelectorAll(".refresh-card").forEach(button => {
        button.addEventListener("click", function () {
            let row = this.closest("tr");
            let cardName = row.dataset.card;
            let storeName = row.dataset.store;
            let lastUpdatedCell = row.querySelector(".last-updated");

            console.log(`🔄 Refreshing ${cardName} at ${storeName}...`);
            button.disabled = true;
            button.innerText = "Refreshing...";

            fetch(`/refresh-card`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ store: storeName, card: cardName })
            })
                .then(response => response.json())
                .then(data => {
                    console.log(`✅ Updated ${cardName}:`, data);

                    // Update UI
                    row.cells[2].innerText = data.price;
                    row.cells[3].innerText = data.stock;
                    row.cells[4].innerText = data.condition;
                    row.cells[5].innerText = data.finish;
                    lastUpdatedCell.innerText = new Date().toLocaleString();

                    button.disabled = false;
                    button.innerText = "Refresh";
                })
                .catch(error => {
                    console.error("❌ Error refreshing:", error);
                    button.disabled = false;
                    button.innerText = "Refresh";
                });
        });
    });
});
