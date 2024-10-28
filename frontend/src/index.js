// src/index.js
// Entry point of the application

import React from 'react';
import { createRoot } from 'react-dom/client'; // Import createRoot
import App from './App'; // Import the main App component

// Create a root element
const rootElement = document.getElementById('root');
const root = createRoot(rootElement); // Create a root

// Render the App component into the root DOM element
root.render(
    <React.StrictMode>
        <App />
    </React.StrictMode>
);
