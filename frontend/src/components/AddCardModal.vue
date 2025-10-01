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
            <input type="text" class="form-control" id="cardName" v-model="cardName" list="cardNameDatalist" autocomplete="off" />
            <datalist id="cardNameDatalist">
              <option v-for="name in searchResults" :key="name" :value="name"></option>
            </datalist>
          </div>

          <!-- Amount -->
          <div class="mb-3">
            <label for="amount" class="form-label">Amount to Track</label>
            <input type="number" class="form-control" id="amount" v-model.number="amount" min="1" />
          </div>

          <!-- Set Dropdown -->
          <div class="mb-3">
            <label for="set" class="form-label">Set (Optional)</label>
            <select id="set" class="form-select" v-model="selectedSet">
              <option value="">Any Set</option>
              <option v-for="set in setOptions" :key="set" :value="set">
                {{ set.toUpperCase() }}
              </option>
            </select>
          </div>

          <!-- Collector Number Dropdown -->
          <div class="mb-3">
            <label for="collectorNumber" class="form-label">Collector # (Optional)</label>
            <select id="collectorNumber" class="form-select" v-model="selectedCollectorNumber" :disabled="!selectedSet">
              <option value="">Any Number</option>
              <option v-for="num in collectorNumberOptions" :key="num" :value="num">
                {{ num }}
              </option>
            </select>
          </div>

          <!-- Finish Dropdown -->
          <div class="mb-3">
            <label for="finish" class="form-label">Finish (Optional)</label>
            <select id="finish" class="form-select" v-model="selectedFinish" :disabled="!selectedCollectorNumber">
              <option value="">Any Finish</option>
              <option v-for="finish in finishOptions" :key="finish" :value="finish">
                {{ finish }}
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
import { ref, computed, watch, onMounted, onUnmounted } from 'vue';
import { useSocket } from '@/composables/useSocket';
import { debounce } from '@/utils/debounce';

const emit = defineEmits(['close', 'save-card']);

// Get the entire socket manager from the composable.
const socketManager = useSocket();

// --- Local State ---
const cardName = ref('');
const searchResults = ref([]); // For autocomplete suggestions

// Component State
const amount = ref(1);
const printings = ref([]); // To store all printings for the selected card
const error = ref(null);

// Selected values from dropdowns
const selectedSet = ref('');
const selectedCollectorNumber = ref('');
const selectedFinish = ref('');

// --- Autocomplete and Printing Fetch Logic ---

// 1. Debounce the search function to avoid spamming the server while typing.
const debouncedSearch = debounce((query) => {
  if (query.length > 2 && socketManager.socket) {
    console.log(`[AddCardModal] 📡 Searching for card names matching: ${query}`);
    socketManager.socket.emit('search_card_names', { query });
  }
}, 300);

// 2. Watch the cardName input and trigger the debounced search.
watch(cardName, (newQuery) => {
  debouncedSearch(newQuery);
  // When the card name changes, also fetch its printings.
  printings.value = [];
  if (newQuery && socketManager.socket) {
    console.log(`[AddCardModal] 📡 Requesting printings for card: ${newQuery}`);
    socketManager.socket.emit('get_card_printings', { card_name: newQuery });
  }
});

// 3. Listen for backend responses for both search and printings.
const handlePrintingsData = (data) => {
  console.log(`[AddCardModal] 📩 Received printings data for: ${data.card_name}`, data.printings);
  if (data.card_name === cardName.value) {
    printings.value = data.printings;
  }
};

onMounted(() => {
  socketManager.socket?.on('card_printings_data', handlePrintingsData);
  socketManager.socket?.on('card_name_search_results', (data) => {
    console.log(`[AddCardModal] 📩 Received search results:`, data.card_names);
    searchResults.value = data.card_names;
  });
});

onUnmounted(() => {
  socketManager.socket?.off('card_printings_data', handlePrintingsData);
  socketManager.socket?.off('card_name_search_results');
});

// 4. Create computed properties to derive dropdown options from the stored data

// Options for the "Set" dropdown (unique set codes)
const setOptions = computed(() => {
  const sets = new Set(printings.value.map(p => p.set_code));
  return Array.from(sets);
});

// Options for "Collector Number", filtered by the selected set
const collectorNumberOptions = computed(() => {
  if (!selectedSet.value) return [];
  return printings.value
    .filter(p => p.set_code === selectedSet.value)
    .map(p => p.collector_number);
});

// Options for "Finish", filtered by the selected set and collector number
const finishOptions = computed(() => {
  if (!selectedSet.value || !selectedCollectorNumber.value) return [];
  const printing = printings.value.find(
    p => p.set_code === selectedSet.value && p.collector_number === selectedCollectorNumber.value
  );
  return printing ? printing.finishes : [];
});

// --- Watchers to reset dependent dropdowns ---

watch(selectedSet, () => {
  // When the set changes, reset the collector number and finish
  selectedCollectorNumber.value = '';
  selectedFinish.value = '';
});

watch(selectedCollectorNumber, () => {
  // When the collector number changes, reset the finish
  selectedFinish.value = '';
});

// --- Save Logic ---

const handleSave = () => {
  error.value = null;
  if (amount.value < 1) {
    error.value = 'Amount must be at least 1.';
    return;
  }

  const cardData = {
    card: cardName.value,
    amount: amount.value,
    card_specs: {
      set_code: selectedSet.value,
      collector_number: selectedCollectorNumber.value,
      finish: selectedFinish.value,
    },
  };

  console.log(`[AddCardModal] 💾 Emitting save-card event with data:`, cardData);
  emit('save-card', cardData);
  emit('close');
};
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
