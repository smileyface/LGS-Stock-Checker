<template>
    <div class="login-container">
        <div class="login-box">
            <h2 class="text-center mb-4">LGS Stock Checker</h2>
            <form @submit.prevent="handleLogin">
                <div class="mb-3">
                    <label for="username" class="form-label">Username</label>
                    <input id="username" v-model="username" type="text" class="form-control" required>
                </div>
                <div class="mb-3">
                    <label for="password" class="form-label">Password</label>
                    <input id="password" v-model="password" type="password" class="form-control" required>
                </div>
                <div v-if="error" class="alert alert-danger">
                    {{ error }}
                </div>
                <button type="submit" class="btn btn-primary w-100" :disabled="isLoading">
                    {{ isLoading ? 'Logging in...' : 'Login' }}
                </button>
            </form>
            <div class="text-center mt-3">
                <small>Don't have an account? <RouterLink to="/register">Create one here</RouterLink></small>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref } from 'vue';
import { authStore } from '../stores/auth.js';
import { RouterLink } from 'vue-router';
import { createUserSchema, createLoginUserMessage, createLoginUserPayload } from '../schema/server_types.js';

const username = ref('');
const password = ref('');
const error = ref(null);
const isLoading = ref(false);

async function handleLogin() {
    isLoading.value = true;
    error.value = null;
    try {
        // 1. Build the User Schema
        // (Assuming createUserSchema takes a string based on your output, 
        // if it expects an object, use { username: username.value })
        const user = createUserSchema(username.value); 

        // 2. Build the Payload (Wrap arguments in an object!)
        const payload = createLoginUserPayload({
            user: user,
            password: password.value
        });

        // 3. Build the Message Envelope (Wrap arguments in an object!)
        const loginMessage = createLoginUserMessage({
            payload: payload
            // Note: If your factory requires the 'name' property, add it here:
            // name: "login_user" 
        });

        localStorage.setItem("username", username.value);
        await authStore.login(loginMessage);
        
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