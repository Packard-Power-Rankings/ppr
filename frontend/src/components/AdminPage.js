// src/components/AdminPage.js
import React from 'react';
import SportForm from './SportForm'; // Import the SportForm component

const AdminPage = () => {
    return (
        <div>
            <h1>Admin Page</h1>

            {/* Include the SportForm component here */}
            <h2>Upload New Sports Data</h2>
            <SportForm />

            {/* You can remove the sports data table */}
        </div>
    );
};

export default AdminPage;
