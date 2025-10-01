<template>
  <div class="modal fade" ref="editCardModalRef" tabindex="-1" aria-labelledby="editCardModalLabel" aria-hidden="true">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title" id="editCardModalLabel">Edit: {{ cardToEdit.card_name }}</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body">
          <form v-if="editableCard" @submit.prevent="submitUpdate">
            <div class="mb-3">
              <label for="editCardAmount" class="form-label">Amount</label>
              <input type="number" class="form-control" id="editCardAmount" v-model.number="editableCard.amount" min="1" required>
            </div>
            <h6 class="mt-4">Specifications</h6>
            <p class="text-muted small">Currently, only editing the first specification is supported.</p>
            
            <!-- Set Dropdown -->
            <div class="mb-3">
              <label for="edit_set_code" class="form-label">Set Code</label>
              <select id="edit_set_code" class="form-select" v-model="editableCard.specifications[0].set_code">
                <option value="">Any Set</option>
                <option v-for="set in setOptions" :key="set" :value="set">
                  {{ set.toUpperCase() }}
                </option>
              </select>
            </div>
            <!-- Collector Number Dropdown -->
            <div class="mb-3">
              <label for="edit_collector_number" class="form-label">Collector Number</label>
              <select id="edit_collector_number" class="form-select" v-model="editableCard.specifications[0].collector_number" :disabled="!editableCard.specifications[0].set_code">
                <option value="">Any Number</option>
                <option v-for="num in collectorNumberOptions" :key="num" :value="num">
                  {{ num }}
                </option>
              </select>
            </div>
            <!-- Finish Dropdown -->
            <div class="mb-3">
              <label for="edit_finish" class="form-label">Finish</label>
              <select class="form-select" id="edit_finish" v-model="editableCard.specifications[0].finish" :disabled="!editableCard.specifications[0].collector_number">
                <option value="">Any Finish</option>
                <option v-for="finish in finishOptions" :key="finish" :value="finish">
                  {{ finish }}
                </option>
              </select>
            </div>
          </form>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
          <button type="button" class="btn btn-primary" @click="submitUpdate">Save Changes</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch, defineProps, defineEmits, defineExpose } from 'vue';
import { Modal } from 'bootstrap';
import { useCardPrintings } from '@/composables/useCardPrintings';

const props = defineProps({
  cardToEdit: {
    type: Object,
    required: true
  }
});

const emit = defineEmits(['update-card']);

const editCardModalRef = ref(null);
let modalInstance = null;

const editableCard = ref(null);

// --- Card Printings Logic (from composable) ---
// We need a separate ref for the card name to pass to the composable.
const cardNameForPrintings = ref('');

const { 
  setOptions, 
  collectorNumberOptions, 
  finishOptions,
  fetchPrintings,
} = useCardPrintings(cardNameForPrintings, computed(() => editableCard.value?.specifications[0]?.set_code), computed(() => editableCard.value?.specifications[0]?.collector_number));

// --- Save Logic ---

function submitUpdate() {
  const payload = {
    card: props.cardToEdit.card_name, // The original name to find the card
    update_data: {
      amount: editableCard.value.amount,
      specifications: [editableCard.value.specifications[0]] // The UI only supports editing the first spec
    }
  };
  emit('update-card', payload);
  modalInstance.hide();
}

// --- Modal Lifecycle & Data Fetching ---

function show() {
  // Deep copy to avoid mutating the prop directly
  editableCard.value = JSON.parse(JSON.stringify(props.cardToEdit));
  
  // Ensure specifications is an array with at least one object for the form
  if (!editableCard.value.specifications || editableCard.value.specifications.length === 0) {
    editableCard.value.specifications = [{ set_code: '', collector_number: '', finish: '' }];
  }

  // Trigger the fetch for printings. We can't use the watcher in the composable
  // on initial show, so we call the fetch function directly.
  cardNameForPrintings.value = props.cardToEdit.card_name;
  fetchPrintings(props.cardToEdit.card_name);

  modalInstance.show();
}

onMounted(() => {
  modalInstance = new Modal(editCardModalRef.value);
});

// --- Watchers to reset dependent dropdowns ---

watch(() => editableCard.value?.specifications[0]?.set_code, (newValue, oldValue) => {
  // Only reset if it's a user-driven change, not the initial load.
  // On initial load, oldValue will be undefined.
  if (oldValue !== undefined && editableCard.value) {
    editableCard.value.specifications[0].collector_number = '';
  }
});

watch(() => editableCard.value?.specifications[0]?.collector_number, (newValue, oldValue) => {
  if (oldValue !== undefined && editableCard.value) {
    editableCard.value.specifications[0].finish = '';
  }
});

defineExpose({
  show
});
</script>