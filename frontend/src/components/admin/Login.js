// src/components/admin/Login.js
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const Login = ({ onLoginSuccess }) => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [errorMessage, setErrorMessage] = useState('');
    const navigate = useNavigate(); // Get the navigate function

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
                // Save token to local storage or context
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
