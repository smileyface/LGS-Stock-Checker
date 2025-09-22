import { reactive } from 'vue';
import axios from 'axios';
import router from '../router'; // Import router to handle redirects

// A simple reactive object to act as our authentication store
export const authStore = reactive({
    isAuthenticated: false,
    user: null,

    async checkAuthStatus() {
        try {
            // We reuse the user_data endpoint. If it returns data, the user has an active session.
            const response = await axios.get('/api/user_data');
            if (response.data && response.data.username) {
                this.isAuthenticated = true;
                this.user = response.data;
            } else {
                throw new Error('Not authenticated');
            }
        } catch (error) {
            // A 401 or other error means the user is not authenticated
            this.isAuthenticated = false;
            this.user = null;
        }
    },

    async login(credentials) {
        // The backend needs to handle this POST request and set the session cookie
        await axios.post('/api/login', credentials);
        await this.checkAuthStatus(); // Verify login was successful
        if (this.isAuthenticated) {
            router.push({ name: 'Dashboard' }); // Redirect on success
        }
    },

    async logout() {
        await axios.post('/api/logout'); // Tell backend to clear the session
        this.isAuthenticated = false;
        this.user = null;
        router.push({ name: 'Login' }); // Redirect to login page
    }
});

