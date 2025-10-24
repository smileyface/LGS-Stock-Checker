<template>
    <BaseLayout :title="pageTitle">
        <AddCardModal v-if="isAddModalVisible" @save-card="saveCard" @close="isAddModalVisible = false" />
        <EditCardModal v-if="cardToEdit" :card-to-edit="cardToEdit" ref="editCardModalRef" @update-card="updateCard" /> 
        <InStockModal 
            ref="inStockModalRef"
            :card-name="selectedCardForStock"
            :items="availableItemsForModal"
        />
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
                <tbody @dblclick="handleTableDoubleClick">
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
import InStockModal from '../components/InStockModal.vue';
import { authStore } from '../stores/auth';
import { useSocket } from '../composables/useSocket';

const username = computed(() => authStore.user?.username || '');
const pageTitle = ref('Dashboard');
const allStores = computed(() => authStore.user?.stores || []);

// --- Modal State ---
const inStockModalRef = ref(null);
const selectedCardForStock = ref('');
const availableItemsForModal = ref([]);

const editCardModalRef = ref(null);
const cardToEdit = ref(null);
const isAddModalVisible = ref(false);

// Use the composable to get reactive state and methods
const { 
    trackedCards, 
    availabilityMap, 
    deleteCard, 
    saveCard, 
    updateCard,
    getStockData
} = useSocket();

function renderAvailability(cardName) {
    const availability = availabilityMap.value[cardName];

    // 1. Explicitly check for 'searching' status
    if (availability && availability.status === 'searching') {
        return `<span class="badge bg-info text-dark d-inline-flex align-items-center">
                    <span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>
                    Searching</span>`;
    }

    // 2. Check for 'Available' status
    if (availability && availability.status === 'completed' && availability.items && availability.items.length > 0) {
        return `<span class="badge bg-success available-badge" style="cursor: pointer;" data-card-name="${cardName}">Available</span>`;
    }

    // 3. Default to 'Not Available' for all other cases (e.g., not yet searched, or completed with no items)
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

function showInStockModal(cardName) {
    console.log(`🖱️ Opening in-stock modal for: ${cardName}`);
    const availability = availabilityMap.value[cardName];
    selectedCardForStock.value = cardName;
    availableItemsForModal.value = availability?.items || [];
    nextTick(() => {
        inStockModalRef.value?.show();
    });
}

function handleTableDoubleClick(event) {
    // Check if the clicked element (or its parent) is an 'available-badge'
    console.log("handleTableDoubleClick")
    const badge = event.target.closest('.available-badge');

    if (badge) {
        const cardName = badge.dataset.cardName;
        if (cardName) {
            getStockData(cardName);
            showInStockModal(cardName);
        }
    }
}
</script>

<style scoped>
.action-buttons {
  display: flex;
  gap: 0.25rem; /* Adds a small, consistent space between buttons */
  white-space: nowrap; /* This is the key: it prevents the buttons from wrapping */
}
</style>