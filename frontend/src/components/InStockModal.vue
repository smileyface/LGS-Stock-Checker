<template>
  <div class="modal fade" id="inStockModal" tabindex="-1" aria-labelledby="inStockModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-lg" ref="inStockModalElement">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title" id="inStockModalLabel">Stock for: {{ cardName }}</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body">
          <div v-if="!items || items.length === 0" class="text-center">
            <p>No stock found for this card in your selected stores.</p>
          </div>
          <ul v-else class="list-group">
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
import { computed, ref, onMounted, defineExpose } from 'vue';
import { Modal } from 'bootstrap';

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

const inStockModalElement = ref(null);
let modalInstance = null;

onMounted(() => {
  modalInstance = new Modal(inStockModalElement.value);
});

function show() {
  modalInstance.show();
}

defineExpose({ show });

// Sort items by price, lowest first
const sortedItems = computed(() => {
  // Create a shallow copy to avoid mutating the original prop array
  return [...props.items].sort((a, b) => a.price - b.price);
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