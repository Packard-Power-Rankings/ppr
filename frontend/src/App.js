// src/App.js
// Main application component

import React from 'react';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import Home from './components/Home';
import About from './components/About';
import SportForm from './components/SportForm';
import AdminPage from './components/AdminPage'; // Import the AdminPage component
import './Nav.css'; // Optional: Include any styles for your navigation

const App = () => {
    return (
        <Router>
            <nav>
                <Link to="/">Home</Link>
                <Link to="/sport-form">Sport Form</Link>
                <Link to="/admin">Admin</Link> {/* Link to AdminPage */}
                <Link to="/about">About</Link>
            </nav>
            <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/sport-form" element={<SportForm />} />
                <Route path="/admin" element={<AdminPage />} /> {/* Route for AdminPage */}
                <Route path="/about" element={<About />} />
            </Routes>
        </Router>
    );
};

export default App;
