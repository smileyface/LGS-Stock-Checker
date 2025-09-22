import { createRouter, createWebHistory } from 'vue-router';
import Dashboard from '../views/Dashboard.vue';

const routes = [
    {
        path: '/',
        name: 'Dashboard',
        component: Dashboard,
    },
    // You can add other routes here later, e.g., for a login page
    // {
    //   path: '/login',
    //   name: 'Login',
    //   component: () => import('../views/Login.vue') // Lazy loading
    // }
];

const router = createRouter({
    history: createWebHistory(),
    routes,
});

export default router;