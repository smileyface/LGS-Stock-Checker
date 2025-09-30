<script setup>
import { ref } from 'vue';
import { authStore } from '@/stores/auth'; // Adjust path if needed
import { RouterLink } from 'vue-router';

const username = ref('');
const password = ref('');
const confirmPassword = ref('');
const error = ref(null);
const successMessage = ref(null);

const handleRegister = async () => {
  error.value = null;
  successMessage.value = null;

  if (password.value !== confirmPassword.value) {
    error.value = 'Passwords do not match.';
    return;
  }

  if (!username.value || !password.value) {
    error.value = 'Username and password are required.';
    return;
  }

  try {
    await authStore.register({
      username: username.value,
      password: password.value,
    });
    // The authStore's register method handles the redirect on successful login,
    // so no further action is needed here.
  } catch (e) {
    if (e.response && e.response.data && e.response.data.error) {
      error.value = e.response.data.error; // e.g., "Username already exists"
    } else {
      error.value = 'An unexpected error occurred during registration.';
    }
    console.error('Registration failed:', e);
  }
};
</script>

<template>
  <div class="container mt-5">
    <div class="row justify-content-center">
      <div class="col-md-6">
        <div class="card">
          <div class="card-header">
            <h3>Register New Account</h3>
          </div>
          <div class="card-body">
            <form @submit.prevent="handleRegister">
              <div v-if="error" class="alert alert-danger">{{ error }}</div>
              <div class="mb-3">
                <label for="username" class="form-label">Username</label>
                <input type="text" class="form-control" id="username" v-model="username" required />
              </div>
              <div class="mb-3">
                <label for="password" class="form-label">Password</label>
                <input type="password" class="form-control" id="password" v-model="password" required />
              </div>
              <div class="mb-3">
                <label for="confirmPassword" class="form-label">Confirm Password</label>
                <input type="password" class="form-control" id="confirmPassword" v-model="confirmPassword" required />
              </div>
              <button type="submit" class="btn btn-primary w-100">Register</button>
            </form>
          </div>
          <div class="card-footer text-center">
            <small>Already have an account? <RouterLink to="/login">Log in here</RouterLink></small>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
