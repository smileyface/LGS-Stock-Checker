<template>
    <BaseLayout :title="pageTitle">
        <div class="container mt-4">
            <h1>Dashboard</h1>
            <p>Welcome, <strong>{{ username }}</strong>!</p>

            <h2>Your Tracked Cards</h2>
            <table class="table table-striped table-bordered" id="cardTable">
                <thead>
                    <tr>
                        <th style="width: 60px;"></th> <th>Amount</th>
                        <th>Card Name</th>
                        <th>Set Code</th>
                        <th>Collector Number</th>
                        <th>Finish</th>
                        <th>Available</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="card in trackedCards" :key="card.card_name">
                        <td>
                            <div class="action-buttons">
                                <button class="btn btn-sm btn-light" title="Edit" @click="editCard(card)">✏️</button>
                                <button class="btn btn-sm btn-light" title="Delete" @click="deleteCard(card.card_name)">❌</button>
                            </div>
                        </td>
                        <td>{{ card.amount }}</td>
                        <td>{{ card.card_name }}</td>
                        <td>{{ card.specifications?.[0]?.set_code || "N/A" }}</td>
                        <td>{{ card.specifications?.[0]?.collector_number || "N/A" }}</td>
                        <td>{{ card.specifications?.[0]?.finish || "Non-Foil" }}</td>
                        <td v-html="renderAvailability(card.card_name)"></td>
                    </tr>
                </tbody>
            </table>
            
            <button class="btn btn-success mt-3" @click="showAddCardModal">
                Add Card
            </button>
            
            <div class="mb-3">
                <div class="form-check form-check-inline" v-for="store in allStores" :key="store">
                    <input class="form-check-input" type="checkbox" name="storeFilter" :value="store" :id="'store_' + store">
                    <label class="form-check-label" :for="'store_' + store">{{ store }}</label>
                </div>
            </div>
        </div>
    </BaseLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import BaseLayout from '../components/BaseLayout.vue';
import { io } from 'socket.io-client';

const username = ref('');
const trackedCards = ref([]);
const availabilityMap = ref({});
const pageTitle = ref('Dashboard');
const allStores = ref([]);
const socket = io({ withCredentials: true });

onMounted(() => {
    // We'll need a way to get the username from the session, likely from the backend on initial load.
    // This is a placeholder for that logic.
    // For now, we'll assume the Flask backend serves the username as part of a JSON endpoint.
    fetch('/api/user_data')
        .then(response => response.json())
        .then(data => {
            username.value = data.username;
            allStores.value = data.stores;
        });

    socket.on('cards_data', (data) => {
        trackedCards.value = data.tracked_cards || [];
    });

    socket.on('card_availability_data', (data) => {
        // Logic to update availability map
        const cardName = data.card;
        const storeName = data.store;
        const isAvailable = data.items && data.items.length > 0;
        
        if (!availabilityMap.value[cardName]) {
            availabilityMap.value[cardName] = [];
        }

        const storeIndex = availabilityMap.value[cardName].indexOf(storeName);
        if (isAvailable && storeIndex === -1) {
            availabilityMap.value[cardName].push(storeName);
        } else if (!isAvailable && storeIndex !== -1) {
            availabilityMap.value[cardName].splice(storeIndex, 1);
        }
    });

    socket.emit("get_cards");
    socket.emit("get_card_availability");
});

function renderAvailability(cardName) {
    const stores = availabilityMap.value[cardName];
    if (!stores || stores.length === 0) {
        return '<span class="badge bg-secondary">Not Available</span>';
    }
    return stores.map(store => `<span class="badge bg-success me-1">${store}</span>`).join(' ');
}

function deleteCard(cardName) {
    socket.emit('delete_card', { card: cardName });
}

function editCard(card) {
    // You would typically navigate to a new route here, e.g., using Vue Router
    // router.push({ name: 'EditCard', params: { cardName: card.card_name } });
    console.log(`Editing card: ${card.card_name}`);
}

function showAddCardModal() {
    // Show the add card modal here, which would also be a Vue component.
    console.log('Showing add card modal');
}
</script>