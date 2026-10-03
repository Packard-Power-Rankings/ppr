import axios from 'axios';
import { store } from 'src/store';

const api = axios.create({
    baseURL: process.env.REACT_APP_API_URL || "http://localhost:8000",
    withCredentials: true,
});

api.interceptors.response.use(
    (response) => response,
    (error) => {
        const isLoginRequest = /\/token\/?$/.test(error.config?.url || '');
        if (error.response?.status === 401 &&
            store.getState().isAdmin && !isLoginRequest) {
            store.dispatch({ type: 'logout' });
        }
        return Promise.reject(error);
    },
);

export default api
