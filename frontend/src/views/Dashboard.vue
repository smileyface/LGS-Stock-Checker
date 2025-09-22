<template>
    <BaseLayout :title="pageTitle">
        <AddCardModal ref="addCardModalRef" @save-card="saveCard" />
        <EditCardModal v-if="cardToEdit" :card-to-edit="cardToEdit" ref="editCardModalRef" @update-card="updateCard" />
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
import { ref, onMounted, computed, nextTick } from 'vue';
import BaseLayout from '../components/BaseLayout.vue';
import AddCardModal from '../components/AddCardModal.vue';
import EditCardModal from '../components/EditCardModal.vue';
import { io } from 'socket.io-client';
import { authStore } from '../stores/auth';

const username = computed(() => authStore.user?.username || '');
const trackedCards = ref([]);
const availabilityMap = ref({});
const pageTitle = ref('Dashboard');
const allStores = computed(() => authStore.user?.stores || []);
const socket = io({ withCredentials: true });
const addCardModalRef = ref(null);
const editCardModalRef = ref(null);
const cardToEdit = ref(null);

onMounted(async () => {
    // User and store data are now retrieved from the authStore,
    // which is populated when the application first loads.

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
    cardToEdit.value = card;
    // Use nextTick to ensure the modal component is rendered before we try to show it
    nextTick(() => {
        editCardModalRef.value?.show();
    });
}

function showAddCardModal() {
    addCardModalRef.value?.show();
}

function saveCard(cardData) {
    socket.emit('add_card', cardData);
}

function updateCard(cardData) {
    socket.emit('update_card', cardData);
}
</script>