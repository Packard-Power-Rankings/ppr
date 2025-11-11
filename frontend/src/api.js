import axios from 'axios';

const TOKEN_KEY = 'access_token';

const api = axios.create({
  baseURL: 'http://localhost:8000',
});

const getStoredToken = () => {
  if (typeof window === 'undefined') {
    return null;
  }
  return window.localStorage.getItem(TOKEN_KEY);
};

export const setAuthHeader = (token) => {
  if (token) {
    api.defaults.headers.common.Authorization = `Bearer ${token}`;
  } else {
    delete api.defaults.headers.common.Authorization;
  }
};

api.interceptors.request.use((config) => {
  const token = getStoredToken();
  if (!config.headers) config.headers = {};

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  } else {
    delete config.headers.Authorization;
  }
  return config;
});

const existingToken = getStoredToken();
if (existingToken) {
  setAuthHeader(existingToken);
}

export default api;
