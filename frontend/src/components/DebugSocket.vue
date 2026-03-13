<template>
  <div style="padding: 20px; border: 2px dashed #ccc; margin: 20px; border-radius: 8px;">
    <h2>🔌 Socket Communication Test</h2>
    
    <div style="margin-bottom: 15px;">
      <strong>Status: </strong>
      <span :style="{ color: isConnected ? 'green' : 'red', fontWeight: 'bold' }">
        {{ isConnected ? 'CONNECTED' : 'DISCONNECTED' }}
      </span>
    </div>

    <div style="margin-bottom: 15px; display: flex; gap: 10px;">
      <button @click="testAddCard">Test: Add 'Debug Card'</button>
      <button @click="testDeleteCard">Test: Delete 'Debug Card'</button>
    </div>

    <div>
      <h3>Tracked Cards ({{ trackedCards.length }})</h3>
      <pre style="background: #f4f4f4; padding: 10px; border-radius: 4px; max-height: 200px; overflow: auto;">{{ trackedCards }}</pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useSocket } from '../composables/useSocket';
// Import your TS types if you want to be extra safe, though Vue will infer them
// import type { CardPreferenceSchema } from '../schema/server_types';

// 1. Removed availabilityMap from destructuring
const { isConnected, trackedCards, addCard, deleteCard } = useSocket();

const testAddCard = () => {
  // 2. Removed 'specifications' to perfectly match CardPreferenceSchema
  addCard({
    card: { name: "Debug Card - Black Lotus" },
    amount: 1
  });
};

const testDeleteCard = () => {
  // 3. Passed a full CardPreferenceSchema object instead of a flat string
  deleteCard({
    card: { name: "Debug Card - Black Lotus" },
    amount: 1 // Even for deletion, Pydantic/TS likely requires the full schema shape
  });
};
</script>