import axios from 'axios';
import { store } from 'src/store';

const TOKEN_KEY = 'access_token';

const api = axios.create({
    baseURL: process.env.REACT_APP_API_URL || "http://localhost:8000"
});

export const setAuthHeader = (token) => {
    if (token) {
        localStorage.setItem(TOKEN_KEY, token);
        api.defaults.headers.common.Authorization = `Bearer ${token}`;
    } else {
        localStorage.removeItem(TOKEN_KEY);
        delete api.defaults.headers.common.Authorization;
    }
};

const storedToken = localStorage.getItem(TOKEN_KEY);
if (storedToken) {
    setAuthHeader(storedToken);
}

api.interceptors.request.use((config) => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    } else {
        delete config.headers.Authorization;
    }
    return config;
});

api.interceptors.response.use(
    (response) => response,
    (error) => {
        const isLoginRequest = /\/token\/?$/.test(error.config?.url || '');
        if (error.response?.status === 401 &&
            localStorage.getItem(TOKEN_KEY) && !isLoginRequest) {
            setAuthHeader(null);
            store.dispatch({ type: 'logout' });
        }
        return Promise.reject(error);
    },
);

export default api
