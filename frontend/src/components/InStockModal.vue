<template>
  <div class="modal fade" ref="inStockModalRef" tabindex="-1" aria-labelledby="inStockModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-lg modal-dialog-scrollable">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title" id="inStockModalLabel">Available Stock: {{ cardName }}</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body">
          <div v-if="!sortedItems.length" class="text-center text-muted">
            <p>No available stock details found.</p>
          </div>
          <div v-else>
            <div class="d-flex justify-content-end mb-2">
              <button class="btn btn-sm btn-outline-secondary" @click="toggleSort">
                Sort by Price {{ sortDirection === 'asc' ? '▲' : '▼' }}
              </button>
            </div>
            <ul class="list-group">
              <li v-for="(item, index) in sortedItems" :key="index" class="list-group-item">
                <div class="row g-3 align-items-center">
                  <!-- Card Image -->
                  <div class="col-md-3 col-4">
                    <img :src="getScryfallImage(item.set_code, item.collector_number)" 
                         class="img-fluid rounded" 
                         :alt="`Image of ${cardName}`" 
                         loading="lazy" />
                  </div>
                  <!-- Card Details -->
                  <div class="col-md-9 col-8">
                    <h6 class="mb-1">{{ item.store_name }}</h6>
                    <p class="mb-1 fs-5 fw-bold text-success">${{ item.price.toFixed(2) }}</p>
                    <div class="card-details small text-muted">
                      <span><strong>Set:</strong> {{ item.set_code.toUpperCase() }}</span>
                      <span><strong>#:</strong> {{ item.collector_number }}</span>
                      <span><strong>Finish:</strong> {{ item.finish }}</span>
                    </div>
                  </div>
                </div>
              </li>
            </ul>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, defineProps, defineExpose } from 'vue';
import { Modal } from 'bootstrap';

const props = defineProps({
  cardName: {
    type: String,
    required: true,
  },
  availableItems: {
    type: Array,
    required: true,
  },
});

const inStockModalRef = ref(null);
let modalInstance = null;

// --- Sorting Logic ---
const sortDirection = ref('asc'); // 'asc' for low to high, 'desc' for high to low

const sortedItems = computed(() => {
  // Create a copy to avoid mutating the prop
  const items = [...props.availableItems];
  console.log(items)
  return items.sort((a, b) => {
    if (sortDirection.value === 'asc') {
      return a.price - b.price;
    } else {
      return b.price - a.price;
    }
  });
});

function toggleSort() {
  sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc';
}

// --- Image Logic ---

/**
 * Constructs the URL for a card image from the Scryfall API.
 * @param {string} set - The set code of the card.
 * @param {string} collectorNumber - The collector number of the card.
 * @returns {string} The full URL to the card image.
 */
function getScryfallImage(set, collectorNumber) {
  // Use the normal-sized image for good quality without being too large.
  console.log(`getScryfallImage for ${set} ${collectorNumber}`)
  return `https://api.scryfall.com/cards/${set.toLowerCase()}/${collectorNumber}?format=image&version=normal`;
}

// --- Modal Lifecycle ---

onMounted(() => {
  if (inStockModalRef.value) {
    modalInstance = new Modal(inStockModalRef.value);
  }
});

function show() {
  // Reset sort direction when opening
  sortDirection.value = 'asc';
  modalInstance?.show();
}

defineExpose({
  show,
});
</script>

<style scoped>
.card-details span {
  margin-right: 1rem;
  white-space: nowrap;
}

.img-fluid {
  max-width: 100%;
  height: auto;
  border: 1px solid #dee2e6; /* Add a light border around the image */
}
</style>
