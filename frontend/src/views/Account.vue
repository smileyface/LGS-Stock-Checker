<template>
    <BaseLayout title="Account Settings">
        <div class="container mt-4">
            <h1>Account Settings</h1>
            <p>Logged in as: <strong>{{ username }}</strong></p>

            <hr>

            <div class="row">
                <div class="col-md-6">
                    <h2 class="h4">Update Username</h2>
                    <form @submit.prevent="handleUpdateUsername" class="mb-4">
                        <div class="mb-3">
                            <label for="new_username" class="form-label">New Username</label>
                            <input type="text" id="new_username" class="form-control" v-model="newUsername" placeholder="Enter new username">
                        </div>
                        <button type="submit" class="btn btn-primary">Update Username</button>
                    </form>

                    <h2 class="h4">Update Password</h2>
                    <form @submit.prevent="handleUpdatePassword" class="mb-4">
                        <div class="mb-3">
                            <label for="current_password" class="form-label">Current Password</label>
                            <input type="password" id="current_password" class="form-control" v-model="currentPassword" placeholder="Current Password">
                        </div>
                        <div class="mb-3">
                            <label for="new_password" class="form-label">New Password</label>
                            <input type="password" id="new_password" class="form-control" v-model="newPassword" placeholder="New Password">
                        </div>
                        <button type="submit" class="btn btn-primary">Update Password</button>
                    </form>
                </div>

                <div class="col-md-6">
                    <h2 class="h4">Update Preferred Stores</h2>
                    <form @submit.prevent="handleUpdateStores">
                        <p>Select the stores you want to track card availability from.</p>
                        <div class="list-group mb-3">
                            <label v-for="store in allStores" :key="store" class="list-group-item d-flex align-items-center justify-content-between">
                                <span>{{ store }}</span>
                                <div class="form-check form-switch">
                                    <input class="form-check-input store-checkbox" type="checkbox" name="stores" :value="store" :id="'store_' + store" v-model="selectedStores">
                                </div>
                            </label>
                        </div>
                        <button type="submit" class="btn btn-primary">Save Stores</button>
                    </form>
                </div>
            </div>

            <hr>
            <router-link to="/dashboard" class="btn btn-secondary">Back to Dashboard</router-link>
        </div>
    </BaseLayout>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import BaseLayout from '../components/BaseLayout.vue';
import axios from 'axios';
import { authStore } from '../stores/auth.js';

const username = computed(() => authStore.user?.username || '');
const allStores = ref([]);
const selectedStores = ref([]);

const newUsername = ref('');
const currentPassword = ref('');
const newPassword = ref('');

onMounted(() => {
    async function fetchAllStores() {
        try {
            const response = await axios.get('/api/stores');
            allStores.value = response.data;
            // Initialize selected stores from the auth store
            if (authStore.user && authStore.user.stores) {
                selectedStores.value = [...authStore.user.stores];
            }
        } catch (error) {
            console.error('Failed to fetch store list:', error);
            alert('Could not load the list of available stores.');
        }
    }
    fetchAllStores();
});

async function handleUpdateUsername() {
    if (!newUsername.value) {
        alert('Please enter a new username.');
        return;
    }
    try {
        await axios.post('/api/account/update_username', { new_username: newUsername.value });
        alert('Username updated successfully! Please log in again with your new username.');
        await authStore.logout(); // Force logout after username change
    } catch (error) {
        console.error('Error updating username:', error);
        alert('Failed to update username. It might already be taken.');
    }
}

async function handleUpdatePassword() {
    if (!currentPassword.value || !newPassword.value) {
        alert('Please fill in both current and new password fields.');
        return;
    }
    try {
        await axios.post('/api/account/update_password', {
            current_password: currentPassword.value,
            new_password: newPassword.value
        });
        alert('Password updated successfully!');
        currentPassword.value = '';
        newPassword.value = '';
    } catch (error) {
        console.error('Error updating password:', error);
        alert('Failed to update password. Please check your current password.');
    }
}

async function handleUpdateStores() {
    try {
        await axios.post('/api/account/update_stores', { stores: selectedStores.value });
        // Refresh auth status to get the updated store list in the authStore
        await authStore.checkAuthStatus();
        alert('Preferred stores updated successfully!');
    } catch (error) {
        console.error('Error updating stores:', error);
        alert('Failed to update preferred stores.');
    }
}
</script>