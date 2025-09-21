<template>
  <div class="container">
    <h1>LGS Stock Checker</h1>
    <div class="search-section">
      <input
        v-model="partNumber"
        @keyup.enter="checkStock"
        placeholder="Enter Part Number"
      />
      <button @click="checkStock" :disabled="isLoading">
        {{ isLoading ? 'Checking...' : 'Check Stock' }}
      </button>
    </div>

    <div v-if="error" class="error-message">
      <p>{{ error }}</p>
    </div>

    <div class="results-section">
      <h2>Results:</h2>
      <div id="stockResults">
        <div v-if="isLoading" class="loading-spinner"></div>
        <ul v-else-if="results.length > 0">
          <li v-for="(result, index) in results" :key="index">
            <strong>{{ result.store_name }}:</strong>
            <span v-if="result.stock_status === 'In Stock'">
              In Stock - Price: {{ result.price }}
            </span>
            <span v-else>
              {{ result.stock_status }}
            </span>
          </li>
        </ul>
        <p v-else>No results yet. Enter a part number to begin.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { io } from 'socket.io-client';

const partNumber = ref('');
const results = ref([]);
const isLoading = ref(false);
const error = ref(null);

// The socket connection is established here.
// In production, Nginx proxies this to the backend.
// In development, Vite proxies this if configured, or it connects directly.
const socket = io({ autoConnect: false });

onMounted(() => {
  socket.connect();

  socket.on('connect', () => {
    console.log('Connected to backend via Socket.IO');
    error.value = null;
  });

  socket.on('connect_error', (err) => {
    console.error('Socket.IO connection error:', err.message);
    error.value = 'Could not connect to the server. Please wait and try again.';
    isLoading.value = false;
  });

  socket.on('stock_result', (data) => {
    console.log('Received stock result:', data);
    results.value.push(data);
  });

  socket.on('search_complete', () => {
    console.log('Search complete.');
    isLoading.value = false;
  });
});

onUnmounted(() => {
  socket.disconnect();
});

const checkStock = () => {
  if (!partNumber.value.trim() || isLoading.value) {
    return;
  }
  isLoading.value = true;
  results.value = [];
  error.value = null;
  console.log(`Emitting search_part with part number: ${partNumber.value}`);
  socket.emit('search_part', { part_number: partNumber.value });
};
</script>

<style>
/* Add some basic styling here or link to an external CSS file */
.container { max-width: 800px; margin: 0 auto; padding: 2rem; }
.search-section { display: flex; gap: 1rem; margin-bottom: 2rem; }
.error-message { color: red; }
</style>
