<template>
  <div class="modal-backdrop">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Add New Card</h5>
          <button type="button" class="btn-close" @click="$emit('close')"></button>
        </div>
        <div class="modal-body">
          <div v-if="error" class="alert alert-danger">{{ error }}</div>
          
          <!-- Card Name Input -->
          <div class="mb-3">
            <label for="cardName" class="form-label">Card Name</label>
            <input id="cardName" v-model="cardName" type="text" class="form-control" list="cardNameDatalist" autocomplete="off" />
            <datalist id="cardNameDatalist">
              <option v-for="name in searchResults" :key="name" :value="name"></option>
            </datalist>
          </div>

          <!-- Amount -->
          <div class="mb-3">
            <label for="amount" class="form-label">Amount to Track</label>
            <input id="amount" v-model.number="amount" type="number" class="form-control" min="1" />
          </div>

          <!-- Set Dropdown -->
          <div class="mb-3">
            <label for="set" class="form-label">Set (Optional)</label>
            <select id="set" v-model="selectedSet" class="form-select">
              <option value="">Any Set</option>
              <option v-for="set in setOptions" :key="set" :value="set">
                {{ set.toUpperCase() }}
              </option>
            </select>
          </div>

          <!-- Collector Number Dropdown -->
          <div class="mb-3">
            <label for="collectorNumber" class="form-label">Collector # (Optional)</label>
            <select id="collectorNumber" v-model="selectedCollectorNumber" class="form-select" :disabled="!selectedSet">
              <option value="">Any Number</option>
              <option v-for="num in collectorNumberOptions" :key="num" :value="num">
                {{ num }}
              </option>
            </select>
          </div>

          <!-- Finish Dropdown -->
          <div class="mb-3">
            <label for="finish" class="form-label">Finish (Optional)</label>
            <select id="finish" v-model="selectedFinish" class="form-select" :disabled="!selectedCollectorNumber">
              <option :value="undefined">Any Finish</option>
              <option v-for="finish in finishOptions" :key="finish.id" :value="finish.id">
                {{ finish.name }}
              </option>
            </select>
          </div>

        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="$emit('close')">Close</button>
          <button type="button" class="btn btn-primary" @click="handleSave">Save Card</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue';
import { useSocket } from '@/composables/useSocket';
import { useCardPrintings } from '@/composables/useCardPrintings';
import { debounce } from '@/utils/debounce';
import {createCardPreferenceSchema, 
        createCardSpecificationSchema,
        createCardSchema, 
        createUpdateCardRequestPayload } from '@/schema/server_types.ts';
const emit = defineEmits(['close']);
const socket = useSocket();

// --- Local State ---
const cardName = ref('');
const searchResults = ref([]); // For autocomplete suggestions

// Component State
const amount = ref(1);
const error = ref(null);

// Selected values from dropdowns
const selectedSet = ref('');
const selectedCollectorNumber = ref('');
const selectedFinish = ref(undefined);

// --- Card Printings Logic (from composable) ---
const { 
  setOptions, 
  collectorNumberOptions, 
  finishOptions 
} = useCardPrintings(cardName, selectedSet, selectedCollectorNumber);

// --- Autocomplete and Printing Fetch Logic ---

// 1. Debounce the search function to avoid spamming the server while typing.
const debouncedSearch = debounce((query) => {
if (query.length > 2) {
    console.log(`[AddCardModal] 📡 Searching for: ${query}`);
    // This is now type-safe!
    socket.emitMessage('search_card_names', { query });
  }
}, 300);

// 2. Watch the cardName input and trigger the debounced search.
watch(cardName, (newQuery) => {
  debouncedSearch(newQuery);
  // The useCardPrintings composable will automatically handle fetching printings.
});

onMounted(() => {
  socket.socket?.on('card_name_search_results', (data) => {
    console.log(`[AddCardModal] 📩 Received search results:`, data.card_names);
    searchResults.value = data.card_names;
  });
});

onUnmounted(() => {
  socket.socket?.off('card_name_search_results');
});

// --- Watchers to reset dependent dropdowns ---

watch(selectedSet, () => {
  // When the set changes, reset the collector number and finish
  selectedCollectorNumber.value = '';
  selectedFinish.value = undefined;
});

watch(selectedCollectorNumber, () => {
  // When the collector number changes, reset the finish
  selectedFinish.value = undefined;
});

// --- Save Logic ---

const handleSave = () => {
  // ... validation ...

  error.value = null;
  if (!cardName.value || cardName.value.trim() === '') {
    error.value = 'Card name is required.'; // This triggers the UI update
    return; // This stops the code from sending a message to the server
  }
  
  // 1. Build the leaf nodes (ensure these use the {fields} pattern if they are also auto-gen)
  const spec = createCardSpecificationSchema({
    set_code: selectedSet.value || undefined,
    collector_number: selectedCollectorNumber.value || undefined,
    finish: selectedFinish.value
  });

  const card = createCardSchema(cardName.value);

  // 2. Build the Preference
  const preference = createCardPreferenceSchema({
    card,
    amount: amount.value,
    specifications: spec // check if your backend renamed this to 'specifications' or 'spec'
  });

  // 3. Build the Payload (The one we just fixed!)
  const payload = createUpdateCardRequestPayload({
    command: "add", 
    update_data: preference
  });

  // 4. EMIT
  socket.emitMessage('update_card', payload);
  emit('close');
};

defineExpose({
  searchResults // Expose this for testing
});
</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1050;
}

.modal-dialog {
  width: 100%;
  max-width: 500px;
  margin: 1.75rem auto;
}

.modal-content {
  position: relative;
  display: flex;
  flex-direction: column;
  background-color: #fff;
  border-radius: 0.5rem;
}
</style>
