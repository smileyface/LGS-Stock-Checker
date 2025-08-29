/**
 * Renders the availability data as a series of Bootstrap badges.
 * @param {string[] | undefined} stores - An array of store names where the card is available.
 * @returns {string} - HTML string of badges.
 */
function renderAvailability(stores) {
    if (!stores || stores.length === 0) {
        return '<span class="badge bg-secondary">Not Available</span>';
    }
    // Creates a green badge for each store the card is available in.
    return stores.map(store => `<span class="badge bg-success me-1">${store}</span>`).join(' ');
}

/**
 * Clears and repopulates the main card DataTable with tracked cards and their availability.
 * @param {object} cardData - The main card data object from the server.
 * @param {object} availabilityMap - A map of card names to available stores.
 */
window.updateCardTable = function (cardData, availabilityMap) {
    const table = $('#cardTable').DataTable();
    table.clear();

    if (!cardData || !cardData.tracked_cards) {
        console.warn("updateCardTable called with no card data. Clearing table.");
        table.draw();
        return;
    }

    const tableData = cardData.tracked_cards.map(card => {
        // For each card, look up its availability in the map using its name.
        const availableStores = availabilityMap[card.name] || [];
        return [card.name, card.set_name, renderAvailability(availableStores)];
    });

    table.rows.add(tableData).draw();
};