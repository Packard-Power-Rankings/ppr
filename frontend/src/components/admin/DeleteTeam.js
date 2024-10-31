import React from 'react';

const DeleteTeam = ({ sportType, teamName, onComplete }) => {
    const handleDelete = async () => {
        const confirmDelete = window.confirm(`Are you sure you want to delete ${teamName}?`);
        if (confirmDelete) {
            try {
                const response = await fetch(`/admin/${sportType}/delete/${teamName}`, {
                    method: 'DELETE',
                });
                if (response.ok) {
                    alert(`Team '${teamName}' deleted successfully`);
                    onComplete(); // Exit delete mode
                } else {
                    alert('Failed to delete team');
                }
            } catch (error) {
                console.error('Error deleting team:', error);
            }
        }
    };

    return (
        <div>
            <h2>Delete Team: {teamName}</h2>
            <button onClick={handleDelete}>Confirm Delete</button>
            <button onClick={onComplete}>Cancel</button>
        </div>
    );
};

export default DeleteTeam;
