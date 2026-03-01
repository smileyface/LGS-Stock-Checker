<template>
  <div style="padding: 20px; border: 2px dashed #ccc; margin: 20px; border-radius: 8px;">
    <h2>🔌 Socket Communication Test</h2>
    
    <!-- Connection Status -->
    <div style="margin-bottom: 15px;">
      <strong>Status: </strong>
      <span :style="{ color: isConnected ? 'green' : 'red', fontWeight: 'bold' }">
        {{ isConnected ? 'CONNECTED' : 'DISCONNECTED' }}
      </span>
    </div>

    <!-- Actions -->
    <div style="margin-bottom: 15px; display: flex; gap: 10px;">
      <button @click="testAddCard">Test: Add 'Debug Card'</button>
      <button @click="testDeleteCard">Test: Delete 'Debug Card'</button>
    </div>

    <!-- Data Monitor -->
    <div>
      <h3>Tracked Cards ({{ trackedCards.length }})</h3>
      <pre style="background: #f4f4f4; padding: 10px; border-radius: 4px; max-height: 200px; overflow: auto;">{{ trackedCards }}</pre>
    </div>
    
    <div style="margin-top: 15px;">
      <h3>Availability Map</h3>
      <pre style="background: #f4f4f4; padding: 10px; border-radius: 4px; max-height: 200px; overflow: auto;">{{ availabilityMap }}</pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useSocket } from '../composables/useSocket';

// Destructure the reactive state and methods
const { isConnected, trackedCards, availabilityMap, addCard, deleteCard } = useSocket();

const testAddCard = () => {
  // Emits 'add_card' with a dummy payload to test backend reception
  addCard({
    card: { name: "Debug Card - Black Lotus" },
    amount: 1,
    specifications: []
  });
};

const testDeleteCard = () => {
  // Emits 'delete_card'
  deleteCard("Debug Card - Black Lotus");
};
</script>
