document.addEventListener('DOMContentLoaded', function () {
    const updateUsernameBtn = document.getElementById('updateUsernameBtn');
    if (updateUsernameBtn) {
        updateUsernameBtn.addEventListener('click', function () {
            const url = this.dataset.url;
            const newUsername = document.getElementById("new_username").value;
            fetch(url, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ new_username: newUsername })
            }).then(response => response.json()).then(data => alert(data.message || data.error));
        });
    }

    const updatePasswordBtn = document.getElementById('updatePasswordBtn');
    if (updatePasswordBtn) {
        updatePasswordBtn.addEventListener('click', function () {
            const url = this.dataset.url;
            fetch(url, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    current_password: document.getElementById("current_password").value,
                    new_password: document.getElementById("new_password").value
                })
            }).then(response => response.json()).then(data => alert(data.message || data.error));
        });
    }

    const updateStoresBtn = document.getElementById('updateStoresBtn');
    if (updateStoresBtn) {
        updateStoresBtn.addEventListener('click', function () {
            const selectedStores = Array.from(document.querySelectorAll(".store-checkbox:checked")).map(o => o.value);
            if (typeof socket !== 'undefined' && socket && socket.connected) {
                socket.emit('update_stores', { stores: selectedStores });
            } else {
                alert('Not connected to the server. Please refresh the page.');
            }
        });
    }

    // Listen for the success confirmation from the server
    if (typeof socket !== 'undefined') {
        socket.on('update_stores_success', (data) => alert(data.message));
        socket.on('error', (data) => alert('An error occurred: ' + data.message));
    }
});