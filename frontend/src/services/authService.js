import api from "src/api";
import { store } from "src/store";

const clearSession = () => {
    store.dispatch({ type: "logout" });
};

export const checkAuthentication = async () => {
    try {
        const response = await api.get("/validate-token/");
        if (response.data.status === "valid") {
            store.dispatch({ type: "login" });
            return true;
        }
        clearSession();
        return false;
    } catch (error) {
        console.error("Authentication check failed", error);
        clearSession();
        return false;
    }
};

export const initializeAuth = () => checkAuthentication();

export const loginUser = async (credentials) => {
    try {
        const formData = new URLSearchParams();
        formData.append('username', credentials.username);
        formData.append('password', credentials.password);

        await api.post(
            '/token/',
            formData,
            {
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded"
                }
            }
        );
        store.dispatch({ type: 'login' });
        return true;
    } catch (error) {
        console.error('Login Failed', error);
        return false;
    }
};

export const logoutUser = async () => {
    try {
        await api.post("/logout/");
    } catch (error) {
        console.error("Logout Failed", error);
    } finally {
        clearSession();
    }
    return true;
};
