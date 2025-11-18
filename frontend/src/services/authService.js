import api, { setAuthHeader } from "src/api";
import { store } from "src/store";

const removeToken = () => {
    setAuthHeader(null);
    store.dispatch({ type: "logout" });
};

export const checkAuthentication = async () => {
    const token = localStorage.getItem("access_token");
    if (!token) {
        removeToken();
        return false;
    }
    setAuthHeader(token);

    try {
        const response = await api.get("/validate-token/");
        if (response.data.status === "valid") {
            store.dispatch({ type: "login" });
            return true;
        }
        removeToken();
        return false;
    } catch (error) {
        console.error("Authentication check failed", error);
        removeToken();
        return false;
    }
};

export const initilizeAuth = () => checkAuthentication();

export const loginUser = async (credentials) => {
    try {
        const formData = new URLSearchParams();
        formData.append('username', credentials.username);
        formData.append('password', credentials.password);

        const { data } = await api.post(
            '/token/',
            formData,
            {
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded"
                }
            }
        );
        setAuthHeader(data.access_token);
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
        removeToken();
    }
    return true;
};
