<template>
    <BaseLayout :title="pageTitle">
        <AddCardModal v-if="isAddModalVisible" @save-card="saveCard" @close="isAddModalVisible = false" />
        <EditCardModal v-if="cardToEdit" :card-to-edit="cardToEdit" ref="editCardModalRef" @update-card="updateCard" />
        <div class="container mt-4">
            <h1>Dashboard</h1>
            <p>Welcome, <strong>{{ username }}</strong>!</p>

            <h2>Your Tracked Cards</h2>
            <table class="table table-striped table-bordered" id="cardTable">
                <thead>
                    <tr>
                        <th style="width: 80px;"></th> <th>Amount</th>
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
            
            <button class="btn btn-success mt-3" @click="isAddModalVisible = true">
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
import { authStore } from '../stores/auth';
import { useSocket } from '../composables/useSocket';

const username = computed(() => authStore.user?.username || '');
const pageTitle = ref('Dashboard');
const allStores = computed(() => authStore.user?.stores || []);
const editCardModalRef = ref(null);
const cardToEdit = ref(null);
const isAddModalVisible = ref(false);

// Use the composable to get reactive state and methods
const { 
    trackedCards, 
    availabilityMap, 
    deleteCard, 
    saveCard, 
    updateCard 
} = useSocket();

function renderAvailability(cardName) {
    const availability = availabilityMap.value[cardName];

    if (!availability || availability.status === 'searching') {
        return `<span class="badge bg-info text-dark d-inline-flex align-items-center">
                    <span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>
                    Searching</span>`;
    }

    // If the check is complete and the stores array has items, it's available.
    if (availability.stores && availability.stores.length > 0) {
        return '<span class="badge bg-success">Available</span>';
    }

    // Otherwise, it's not available.
        return '<span class="badge bg-secondary">Not Available</span>';
}

function editCard(card) {
    console.log(`✏️ Opening edit modal for: ${card.card_name}`);
    cardToEdit.value = card;
    // Use nextTick to ensure the modal component is rendered before we try to show it
    nextTick(() => {
        editCardModalRef.value?.show();
    });
}
</script>