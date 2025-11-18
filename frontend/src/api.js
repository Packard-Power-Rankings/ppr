import axios from 'axios';

const TOKEN_KEY = 'access_token';

const api = axios.create({
    baseURL: "http://localhost:8000"
});

export default api