import { createRouter, createWebHistory } from 'vue-router';
import Dashboard from '../views/Dashboard.vue';
import Account from '../views/Account.vue';
import Login from '../views/Login.vue';
import { authStore } from '../stores/auth';

const routes = [
    {
        path: '/',
        redirect: '/dashboard'
    },
    {
        path: '/dashboard',
        name: 'Dashboard',
        component: Dashboard,
        meta: { requiresAuth: true } // This route requires authentication
    },
    {
        path: '/account', // Matches the link in BaseLayout
        name: 'Account',
        component: Account,
        meta: { requiresAuth: true } // This route also requires authentication
    },
    {
        path: '/login',
        name: 'Login',
        component: Login,
        meta: { requiresGuest: true } // Only accessible to unauthenticated users
    }
];

const router = createRouter({
    history: createWebHistory(),
    routes,
});

// This navigation guard runs before every route change.
router.beforeEach((to, from, next) => {
    if (to.meta.requiresAuth && !authStore.isAuthenticated) {
        // If route requires auth and user is not logged in, redirect to login page.
        next({ name: 'Login' });
    } else if (to.meta.requiresGuest && authStore.isAuthenticated) {
        // If user is logged in and tries to access a guest page (like login), redirect to dashboard.
        next({ name: 'Dashboard' });
    } else {
        // Otherwise, allow the navigation.
        next();
    }
});

export default router;
