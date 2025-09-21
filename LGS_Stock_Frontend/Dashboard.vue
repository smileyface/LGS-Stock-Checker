<template>
  <div class="dashboard">
    <h1>Main Dashboard</h1>
    <p>Welcome to your new Vue-powered dashboard!</p>

    <div class="status-card">
      <h2>Backend Status</h2>
      <p v-if="loading">Loading...</p>
      <p v-else-if="error" class="error">Error: {{ error }}</p>
      <pre v-else>{{ backendStatus }}</pre>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const loading = ref(true)
const backendStatus = ref(null)
const error = ref(null)

// This function will be called when the component is first mounted.
onMounted(async () => {
  try {
    // The request goes to '/api/status'. Vite's proxy will forward it.
    const response = await axios.get('/api/status')
    backendStatus.value = response.data
  } catch (err) {
    error.value = err.message || 'Failed to fetch status from backend.'
    console.error(err)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.dashboard {
  padding: 2rem;
  background-color: #ffffff;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

h1 {
  color: #2c3e50;
}

.status-card {
  margin-top: 2rem;
  padding: 1rem;
  background-color: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 4px;
}
.error {
  color: #dc3545;
}
pre {
  background-color: #e9ecef;
  padding: 1rem;
  border-radius: 4px;
}
</style>