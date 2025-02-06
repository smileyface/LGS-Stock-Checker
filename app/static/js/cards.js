document.addEventListener("DOMContentLoaded", function () {
    const table = document.getElementById("cardTable");
    if (!table) return; // ✅ Prevents running on the wrong page

    table.addEventListener("dblclick", function (event) {
        const row = event.target.closest("tr");
        if (row && row.dataset.index) {
            const cardIndex = row.dataset.index;
            window.location.href = `/edit-card/${cardIndex}`; // Redirect to edit page
        }
    });
});
