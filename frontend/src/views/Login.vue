<template>
    <div class="login-container">
        <div class="login-box">
            <h2 class="text-center mb-4">LGS Stock Checker</h2>
            <form @submit.prevent="handleLogin">
                <div class="mb-3">
                    <label for="username" class="form-label">Username</label>
                    <input type="text" class="form-control" id="username" v-model="username" required>
                </div>
                <div class="mb-3">
                    <label for="password" class="form-label">Password</label>
                    <input type="password" class="form-control" id="password" v-model="password" required>
                </div>
                <div v-if="error" class="alert alert-danger">
                    {{ error }}
                </div>
                <button type="submit" class="btn btn-primary w-100" :disabled="isLoading">
                    {{ isLoading ? 'Logging in...' : 'Login' }}
                </button>
            </form>
        </div>
    </div>
</template>

<script setup>
import { ref } from 'vue';
import { authStore } from '../stores/auth';

const username = ref('');
const password = ref('');
const error = ref(null);
const isLoading = ref(false);

async function handleLogin() {
    isLoading.value = true;
    error.value = null;
    try {
        await authStore.login({
            username: username.value,
            password: password.value
        });
        // The store handles redirection on success
    } catch (err) {
        error.value = 'Login failed. Please check your username and password.';
        console.error('Login error:', err);
    } finally {
        isLoading.value = false;
    }
}
</script>

<style scoped>
.login-container { display: flex; justify-content: center; align-items: center; min-height: 100vh; }
.login-box { padding: 2rem; background: white; border-radius: 8px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); width: 100%; max-width: 400px; }
</style>