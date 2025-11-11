import api, { setAuthHeader } from "src/api";
import { store } from "src/store";

const TOKEN_KEY = "access_token";

const removeToken = () => {
    localStorage.removeItem(TOKEN_KEY);
    setAuthHeader(null);
    store.dispatch({ type: "logout" });
};

export const checkAuthentication = async () => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) {
        removeToken();
        return false;
    }

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
        formData.append("username", credentials.username);
        formData.append("password", credentials.password);
        formData.append("grant_type", "password");

        const response = await api.post(
            "/token/",
            formData,
            {
                headers: { "Content-Type": "application/x-www-form-urlencoded" }
            }
        );

        const { access_token: accessToken } = response.data;
        if (!accessToken) {
            throw new Error("No access token returned from login.");
        }

        localStorage.setItem(TOKEN_KEY, accessToken);
        setAuthHeader(accessToken);
        store.dispatch({ type: "login" });
        return true;
    } catch (error) {
        if (error.response) {
            console.error("Login failed:", error.response.status, error.response.data);
        } else if (error.request) {
            console.error("No response from server:", error.message);
        } else {
            console.error("Request setup error:", error.message);
        }
        removeToken();
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
