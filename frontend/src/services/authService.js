import api from "src/api";
import { store } from "src/store";

export const checkAuthentication = async () => {
    try {
        const response = await api.get(
            '/validate-token/',
            { withCredentials: true }
        );

        if (response.data.status === 'valid') {
            store.dispatch({ type: 'login' });
            return true;
        } else {
            store.dispatch({ type: 'logout' });
            return false
        }
    } catch (error) {
        console.error("Authentication check failed", error);
        store.dispatch({ type: 'logout' });
        return false;
    }
};

export const initilizeAuth = () => {
    return checkAuthentication();
};

export const loginUser = async (credentials) => {
  try {
    const formData = new URLSearchParams();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);
    formData.append('grant_type', 'password'); // fine if backend ignores this

    const res = await api.post(
      '/token/',
      formData,
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        // IMPORTANT: no withCredentials here anymore
      }
    );

    // res.data should look like:
    // { message: 'Login successful', access_token: '...' }
    const { access_token } = res.data;

    // store the token in your global state so you can use it later for Authorization headers
    store.dispatch({ type: 'login', payload: access_token });

    return true;
  } catch (error) {
    if (error.response) {
      console.error('Login failed:', error.response.status, error.response.data);
    } else if (error.request) {
      console.error('No response from server:', error.message);
    } else {
      console.error('Request setup error:', error.message);
    }
    return false;
  }
};

export const logoutUser = async () => {
    try {
        await api.post('/logout/', {}, {
            withCredentials: true
        })
        store.dispatch({ type: 'logout' })
        return true;
    } catch (error) {
        console.error('Logout Failed', error);
        return false;
    }
};