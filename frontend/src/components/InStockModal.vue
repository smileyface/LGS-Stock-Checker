<template>
  <div class="modal fade" ref="inStockModalRef" id="inStockModal" tabindex="-1" aria-labelledby="inStockModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-lg" ref="inStockModalElement">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title" id="inStockModalLabel">Stock for: {{ cardName }}</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body">
          <div v-if="!displayItems || displayItems.length === 0" class="text-center">
            <p>No stock found for this card in your selected stores.</p>
          </div>
          <ul v-else class="list-group" id="in-stock-list">
            <li v-for="(item, index) in sortedItems" :key="index" class="list-group-item">
              <div class="row g-3 align-items-center">
                <div class="col-md-9">
                  <h6 class="mb-1">{{ item.store_name }}</h6>
                  <div class="card-details small text-muted">
                    <span><strong>Set:</strong> {{ item.set_code }}</span>
                    <span><strong>Quantity:</strong> {{ item.quantity }}</span>
                  </div>
                </div>
                <div class="col-md-3 text-md-end">
                  <p class="mb-1 fs-5 fw-bold text-success">{{ formatPrice(item.price) }}</p>
                </div>
              </div>
            </li>
          </ul>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted, defineExpose, watch } from 'vue';
import { Modal } from 'bootstrap';
import { useSocket } from '@/composables/useSocket';

const props = defineProps({
  cardName: {
    type: String,
    required: true,
  },
  items: {
    type: Array,
    required: true,
  },
});

const { socket, getStockData } = useSocket();

const inStockModalRef = ref(null);
let modalInstance = null;
const displayItems = ref([]);

onMounted(() => {
  modalInstance = new Modal(inStockModalRef.value);

  // Listen for the detailed stock data from the backend
  socket.on('stock_data', (data) => {
    // Only update if the data is for the currently displayed card
    if (data.card_name === props.cardName) {
      console.log(`📦 Received detailed stock data for ${data.card_name}, updating modal.`);
      displayItems.value = data.items;
    }
  });
});

onUnmounted(() => {
  // Clean up the socket listener when the component is destroyed
  socket.off('stock_data');
  // Dispose of the Bootstrap modal instance to prevent memory leaks
  if (modalInstance) {
    modalInstance.dispose();
    modalInstance = null;
  }
});

// Watch the ref directly to ensure the DOM element is available before initializing Bootstrap Modal
watch(inStockModalRef, (newValue) => {
  if (newValue && !modalInstance) { // Only initialize if element exists and modal not already initialized
    modalInstance = new Modal(newValue);
  }
});

// When the props.items changes (i.e., when the modal is opened with new data),
// update our local displayItems ref. This shows the initial data from the dashboard.
watch(() => props.items, (newItems) => {
  displayItems.value = newItems;
}, { immediate: true });

function show() {
  modalInstance.show();
  // When the modal is shown, request the full, detailed stock data from the backend.
  getStockData(props.cardName);
}

defineExpose({ show });

// Sort items by price, lowest first
const sortedItems = computed(() => {
  // Sort the local displayItems ref
  return [...displayItems.value].sort((a, b) => a.price - b.price);
});

// Helper function to format price
const formatPrice = (price) => {
  if (typeof price !== 'number') {
    return price;
  }
  return `$${price.toFixed(2)}`;
};
</script>

<style scoped>
.card-details span {
  margin-right: 1rem;
}
</style>