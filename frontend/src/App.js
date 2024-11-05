import React, { useState } from 'react';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import Home from './components/Home';
import About from './components/About';
import ThemeToggle from './components/ThemeToggle';
import TeamsPage from './components/user/TeamsPage';
import TeamDetails from './components/user/TeamDetails';
import Login from './components/admin/Login';
import AdminPage from './components/admin/AdminPage';
import './Styles.css';
import './Nav.css';

const App = () => {
    const [isAuthenticated, setIsAuthenticated] = useState(false);

    const handleLoginSuccess = (token) => {
        setIsAuthenticated(true);
        console.log('Logged in successfully, token:', token);
        // Perform any additional setup after login (e.g., user info fetch)
    };

    const handleLogout = () => {
        setIsAuthenticated(false);
        localStorage.removeItem('access_token'); // Optionally remove the token if stored in localStorage
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
                <Route path="/login" element={<Login onLoginSuccess={handleLoginSuccess} />} />
                <Route
                    path="/admin"
                    element={isAuthenticated ? <AdminPage /> : <Login onLoginSuccess={handleLoginSuccess} />}
                />
                <Route path="/:sportType" element={<TeamsPage />} />
                <Route path="/user/:sportType/:teamName" element={<TeamDetails />} />
            </Routes>
        </Router>
    );
};

export default App;
