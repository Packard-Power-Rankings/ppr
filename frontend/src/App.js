import React, { useState } from 'react';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import Home from './components/Home';
import About from './components/About';
import Login from './components/Login';
import AdminPage from './components/AdminPage';
import TeamsPage from './components/TeamsPage';
import TeamDetails from './components/TeamDetails';
import ThemeToggle from './components/ThemeToggle';
import './Styles.css';
import './Nav.css';

const App = () => {
    const [isLoggedIn, setIsLoggedIn] = useState(false);

    // Handle login
    const handleLogin = (status) => {
        setIsLoggedIn(status);
    };

    // Handle logout
    const handleLogout = () => {
        setIsLoggedIn(false);
    };

    return (
        <Router>
            <nav>
                <Link to="/" className="nav-label">Packard Power Rankings</Link>
                <Link to="/">Home</Link>
                <Link to="/about">About</Link>
                {isLoggedIn && <Link to="/admin">Admin</Link>}
                {isLoggedIn ? (
                    <button onClick={handleLogout}>Logout</button>
                ) : (
                    <Link to="/login">Login</Link>
                )}
            </nav>
            <ThemeToggle />
            <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/admin" element={isLoggedIn ? <AdminPage /> : <Login onLogin={handleLogin} />} />
                <Route path="/about" element={<About />} />
                <Route path="/login" element={<Login onLogin={handleLogin} />} />
                <Route path="/:sportType" element={<TeamsPage />} />
                <Route path="/user/:sportType/:teamName" element={<TeamDetails />} />
            </Routes>
        </Router>
    );
};

export default App;
