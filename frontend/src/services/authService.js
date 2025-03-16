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

        await api.post(
            '/token/', formData,
            {
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                withCredentials: true
            }
        )
        // console.log(response);
        store.dispatch({ type: 'login' });
        return true;
    } catch (error) {
        console.error('Login Failed', error);
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