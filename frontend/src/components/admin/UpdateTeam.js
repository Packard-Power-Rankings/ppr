// src/components/admin/UpdateTeam.js
import React, { useState } from 'react';

const UpdateTeam = ({ initialTeams, onUpdateSubmit }) => {
    const [teamDetails, setTeamDetails] = useState(initialTeams);
    const [errorMessage, setErrorMessage] = useState('');

    const handleDetailChange = (index, field, value) => {
        const newDetails = [...teamDetails];
        
        // Check for 'power_ranking' to ensure valid number
        if (field === 'power_ranking') {
            const parsedValue = parseFloat(value);
            newDetails[index][field] = isNaN(parsedValue) ? '' : parsedValue; // Ensure no NaN value is set
        } else {
            newDetails[index][field] = value;
        }
        
        setTeamDetails(newDetails);
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        
        // Check for required fields
        for (const team of teamDetails) {
            if (!team.team_name || !team.division || !team.conference || !team.state) {
                setErrorMessage('Please fill in all required fields.');
                return;
            }
    
            // Validate power_ranking to ensure it's a valid number
            if (isNaN(team.power_ranking) || team.power_ranking === '') {
                setErrorMessage('Please provide a valid Power Ranking.');
                return;
            }
        }
    
        // Log the payload before submitting
        console.log("Submitting teams data:", teamDetails);
    
        // Submit data if valid
        onUpdateSubmit(teamDetails);
    };

    return (
        <div>
            <h2>Update Team Information</h2>
            <form onSubmit={handleSubmit}>
                {teamDetails.map((team, index) => (
                    <div key={index}>
                        <input
                            type="text"
                            placeholder="Team Name"
                            value={team.team_name}
                            onChange={(e) => handleDetailChange(index, 'team_name', e.target.value)}
                            required
                        />
                        <input
                            type="text"
                            placeholder="Division"
                            value={team.division}
                            onChange={(e) => handleDetailChange(index, 'division', e.target.value)}
                        />
                        <input
                            type="text"
                            placeholder="Conference"
                            value={team.conference}
                            onChange={(e) => handleDetailChange(index, 'conference', e.target.value)}
                        />
                        <input
                            type="number"
                            placeholder="Power Ranking"
                            value={team.power_ranking}
                            onChange={(e) => handleDetailChange(index, 'power_ranking', e.target.value)}
                        />
                        <input
                            type="text"
                            placeholder="State"
                            value={team.state}
                            onChange={(e) => handleDetailChange(index, 'state', e.target.value)}
                        />
                    </div>
                ))}
                <button type="submit">Update Teams</button>
                {errorMessage && <p style={{ color: 'red' }}>{errorMessage}</p>}
            </form>
        </div>
    );
};

export default UpdateTeam;
