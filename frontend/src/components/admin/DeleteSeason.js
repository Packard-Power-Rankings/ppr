// src/components/admin/DeleteSeason.js
import React from 'react';

const DeleteSeason = ({ seasonName, onComplete }) => {
    const handleDelete = async () => {
        const confirmDelete = window.confirm(`Are you sure you want to delete the season: ${seasonName}?`);
        if (confirmDelete) {
            const token = localStorage.getItem('access_token');  // Get token from localStorage
            if (!token) {
                alert('Unauthorized: No token found');
                return;
            }

            try {
                const response = await fetch(`http://localhost:8000/clear_season/`, {
                    method: 'DELETE',
                    headers: {
                        'Authorization': `Bearer ${token}`,  // Pass token in Authorization header
                        'Content-Type': 'application/json',
                    },
                });

                if (response.ok) {
                    alert(`Season '${seasonName}' deleted successfully`);
                    // Check if onComplete is a function before calling it
                    if (typeof onComplete === 'function') {
                        onComplete(); // Exit delete mode
                    }
                } else {
                    alert('Failed to delete season');
                }
            } catch (error) {
                console.error('Error deleting season:', error);
            }
        }
    };

    return (
        <div>
            <h2>Delete Season: {seasonName}</h2>
            <button onClick={handleDelete}>Confirm Delete</button>
        </div>
    );
};

export default DeleteSeason;
