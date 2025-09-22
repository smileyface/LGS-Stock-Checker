import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

import { authStore } from './stores/auth';

import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap'

// Check authentication status before mounting the app.
// This prevents a flicker of a protected page before redirecting to login.
authStore.checkAuthStatus().then(() => {
    createApp(App)
        .use(router)
        .mount('#app');
});
