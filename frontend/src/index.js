// src/index.js

import React from 'react';
import ReactDOM from 'react-dom';
import App from './App'; // Import the main App component
//import './index.css';    // Optional: import any CSS styles if you have

// Render the App component into the root DOM element
ReactDOM.render(
    <React.StrictMode>
        <App />
    </React.StrictMode>,
    document.getElementById('root') // Ensure you have an element with id 'root' in index.html
);
