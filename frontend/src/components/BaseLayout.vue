<template>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container-fluid">
            <a class="navbar-brand" href="/">LGS Tracker</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav"
                aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav me-auto mb-2 mb-lg-0">
                    <li class="nav-item">
                        <router-link class="nav-link" to="/dashboard">Dashboard</router-link>
                    </li>
                    <li class="nav-item">
                        <router-link class="nav-link" to="/account">Account</router-link>
                    </li>
                </ul>
                <ul class="navbar-nav">
                    <li class="nav-item">
                        <button class="btn btn-link nav-link" @click="handleLogout">Logout</button>
                    </li>
                </ul>
            </div>
        </div>
    </nav>
    <div class="container my-4">
        <slot></slot>
    </div>
</template>

<script setup>
import { authStore } from '../stores/auth';

defineProps({
    title: {
        type: String,
        default: 'LGS Stock Checker'
    }
});
</script>

<style scoped></style>