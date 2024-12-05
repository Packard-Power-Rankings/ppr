import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import Home from './components/Home';
import About from './components/About';
import ThemeToggle from './components/ThemeToggle';
import TeamsPage from './components/user/TeamsPage';
import TeamDetails from './components/user/TeamDetails';
import Login from './components/admin/Login';
import AdminPage from './components/admin/AdminPage';
import jwtDecode from 'jwt-decode';
import './Styles.css';
import './Nav.css';

const App = () => {
    const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem('access_token'));

    const isTokenExpired = (token) => {
        try {
            const decoded = jwtDecode(token);
            const currentTime = Date.now() / 1000; // Current time in seconds
            return decoded.exp < currentTime;
        } catch (error) {
            return true; // Treat invalid or missing token as expired
        }
    };

    useEffect(() => {
        const token = localStorage.getItem('access_token');
        if (!token || isTokenExpired(token)) {
            handleLogout(); // Logout if token is expired or missing
        }
    }, []);

    const handleLoginSuccess = (token) => {
        setIsAuthenticated(true);
        localStorage.setItem('access_token', token); // Save the token for future use
        console.log('Logged in successfully, token:', token);
    };

    const handleLogout = () => {
        setIsAuthenticated(false);
        localStorage.removeItem('access_token'); // Remove the token from local storage on logout
    };

    return (
        <Router>
            <nav>
                <Link to="/" className="nav-label">Packard Power Rankings</Link>
                <Link to="/">Home</Link>
                <Link to="/about">About</Link>
                {isAuthenticated && <Link to="/admin">Admin</Link>}
                {isAuthenticated ? (
                    <button onClick={handleLogout}>Logout</button>
                ) : (
                    <Link to="/login">Login</Link>
                )}
            </nav>
            <ThemeToggle />
            <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/about" element={<About />} />
                <Route
                    path="/login"
                    element={<Login onLoginSuccess={handleLoginSuccess} />}
                />
                <Route
                    path="/admin"
                    element={
                        isAuthenticated ? (
                            <AdminPage />
                        ) : (
                            <Login onLoginSuccess={handleLoginSuccess} />
                        )
                    }
                />
                <Route path="/user/:sportType" element={<TeamsPage />} />
                <Route path="/user/:sportType/:teamName" element={<TeamDetails />} />
            </Routes>
        </Router>
    );
};

export default App;
