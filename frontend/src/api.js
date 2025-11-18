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

export default api
