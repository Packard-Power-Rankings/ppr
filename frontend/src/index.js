// src/index.js
// Entry point of the application

import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';

// Create a root element
const rootElement = document.getElementById('root');
const root = createRoot(rootElement);

// Render the App component into the root DOM element
root.render(
    <React.StrictMode>
        <App />
    </React.StrictMode>
);
