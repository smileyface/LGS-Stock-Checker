<template>
    <BaseLayout title="Your Card List">
        <div class="container mt-4">
            <h2>Your Card List</h2>
            <div v-if="cards.length">
                <table class="table table-striped" id="cardTable">
                    <thead>
                        <tr>
                            <th>Amount</th>
                            <th>Card Name</th>
                            <th>Set Code</th>
                            <th>Collector Number</th>
                            <th>Finish</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="(card, index) in cards" :key="index" :data-index="index">
                            <td>{{ card.amount }}</td>
                            <td>{{ card.card_name }}</td>
                            <td>{{ card.specifications?.[0]?.set_code || "N/A" }}</td>
                            <td>{{ card.specifications?.[0]?.collector_number || "N/A" }}</td>
                            <td>{{ card.specifications?.[0]?.finish || "Non-Foil" }}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
            <div v-else>
                <p>No cards in your list. Upload a new list to get started.</p>
            </div>

            <h3 class="mt-4">Upload a New Card List</h3>
            <form @submit.prevent="uploadCardFile" enctype="multipart/form-data">
                <div class="mb-3">
                    <label for="card_file" class="form-label">Upload Card List</label>
                    <input class="form-control" type="file" id="card_file" name="card_file" required @change="handleFileUpload">
                </div>
                <button type="submit" class="btn btn-primary">Upload</button>
            </form>
        </div>
    </BaseLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import BaseLayout from '../components/BaseLayout.vue';
import axios from 'axios';
import { io } from 'socket.io-client';

const cards = ref([]);
const file = ref(null);
const socket = io({ withCredentials: true });

onMounted(() => {
    socket.emit('get_cards');
    socket.on('cards_data', (data) => {
        cards.value = data.tracked_cards || [];
    });
});

function handleFileUpload(event) {
    file.value = event.target.files[0];
}

async function uploadCardFile() {
    if (!file.value) {
        alert('Please select a file first.');
        return;
    }

    const formData = new FormData();
    formData.append('card_file', file.value);

    try {
        // The request goes to '/api/upload_cards'. Nginx will proxy this to the backend.
        await axios.post('/api/upload_cards', formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        });
        alert('File uploaded successfully!');
        socket.emit('get_cards'); // Refresh the card list
    } catch (error) {
        console.error('Error uploading file:', error);
        alert('Failed to upload file. Check console for details.');
    }
}
</script>