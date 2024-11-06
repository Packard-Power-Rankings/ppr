// src/components/UpdateTeam.js
import React, { useState } from 'react';

const UpdateTeam = ({ initialTeams, onUpdateSubmit }) => {
    const [teamDetails, setTeamDetails] = useState(initialTeams);
    const [errorMessage, setErrorMessage] = useState('');

    const handleDetailChange = (index, field, value) => {
        const newDetails = [...teamDetails];
        newDetails[index][field] = field === 'power_ranking' ? parseFloat(value) : value;
        setTeamDetails(newDetails);
    };

    const handleSubmit = (e) => {
        e.preventDefault();
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
