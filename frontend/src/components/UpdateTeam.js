import React, { useState } from 'react';

const UpdateTeam = ({ sportType, teamName, onComplete }) => {
    const [teamData, setTeamData] = useState({ /* Initial team data */ });

    const handleInputChange = (e) => {
        setTeamData({ ...teamData, [e.target.name]: e.target.value });
    };

    const handleUpdate = async () => {
        try {
            const response = await fetch(`/admin/${sportType}/update/${teamName}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(teamData),
            });
            if (response.ok) {
                alert(`Team '${teamName}' updated successfully`);
                onComplete(); // Exit update mode
            } else {
                alert('Failed to update team');
            }
        } catch (error) {
            console.error('Error updating team:', error);
        }
    };

    return (
        <div>
            <h2>Update Team: {teamName}</h2>
            <form>
                <input
                    name="field1"
                    placeholder="Field 1"
                    value={teamData.field1 || ''}
                    onChange={handleInputChange}
                />
                <input
                    name="field2"
                    placeholder="Field 2"
                    value={teamData.field2 || ''}
                    onChange={handleInputChange}
                />
                <button type="button" onClick={handleUpdate}>Update Team</button>
                <button type="button" onClick={onComplete}>Cancel</button>
            </form>
        </div>
    );
};

export default UpdateTeam;
