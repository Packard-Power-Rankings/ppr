// src/components/admin/DeleteSeason.js
import React from 'react';

const DeleteSeason = ({ seasonName, onComplete }) => {
    const handleDelete = async () => {
        const confirmDelete = window.confirm(`Are you sure you want to delete the season: ${seasonName}?`);
        if (confirmDelete) {
            try {
                const response = await fetch(`http://localhost:8000/clear_season/`, {
                    method: 'DELETE',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                });
                if (response.ok) {
                    alert(`Season '${seasonName}' deleted successfully`);
                    onComplete(); // Exit delete mode
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
