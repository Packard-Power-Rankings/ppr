import axios from 'axios';

const TOKEN_KEY = 'access_token';

const api = axios.create({
    baseURL: "http://localhost:8000"
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

export default api
