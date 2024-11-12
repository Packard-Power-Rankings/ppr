import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import jwtDecode from 'jwt-decode';

const Login = ({ onLoginSuccess }) => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [errorMessage, setErrorMessage] = useState('');
    const navigate = useNavigate(); // Get the navigate function

    const logout = () => {
        localStorage.removeItem('access_token'); // Clear token
        navigate('/login'); // Redirect to login page
    };

    // Function to check if the token is expired
    const isTokenExpired = (token) => {
        if (!token) return true;
        const decoded = jwtDecode(token);
        const currentTime = Date.now() / 1000; // Current time in seconds
        return decoded.exp < currentTime; // Token expired check
    };

    // Automatically check the token's validity and handle logout
    useEffect(() => {
        const token = localStorage.getItem('access_token');
        if (token && isTokenExpired(token)) {
            logout(); // Log out if the token is expired
        }

        // Optional: Set a timer to periodically check the token's validity
        const intervalId = setInterval(() => {
            const token = localStorage.getItem('access_token');
            if (token && isTokenExpired(token)) {
                logout();
            }
        }, 60000); // Check every minute

        return () => clearInterval(intervalId); // Clean up interval on component unmount
    }, []);

    const handleLogin = async (e) => {
        e.preventDefault();

        try {
            const response = await fetch('http://localhost:8000/admin/token/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    'username': username,
                    'password': password,
                }),
            });

            if (response.ok) {
                const data = await response.json();
                localStorage.setItem('access_token', data.access_token);
                onLoginSuccess(data.access_token); // Notify parent component of login success
                navigate('/admin'); // Redirect to the admin page after login
                setErrorMessage('');
            } else {
                const errorData = await response.json();
                setErrorMessage(errorData.detail || 'Login failed');
            }
        } catch (error) {
            setErrorMessage('An error occurred during login');
            console.error('Error during login:', error);
        }
    };

    return (
        <div>
            <h2>Login</h2>
            <form onSubmit={handleLogin}>
                <div>
                    <label htmlFor="username">Username:</label>
                    <input
                        type="text"
                        id="username"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        required
                    />
                </div>
                <div>
                    <label htmlFor="password">Password:</label>
                    <input
                        type="password"
                        id="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                    />
                </div>
                {errorMessage && <p style={{ color: 'red' }}>{errorMessage}</p>}
                <button type="submit">Login</button>
            </form>
        </div>
    );
};

export default Login;
