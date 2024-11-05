// components/TeamDetails.js
import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';

const TeamDetails = () => {
    const { sportType, teamName } = useParams();
    const [teamData, setTeamData] = useState(null);
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(true);

    const fetchTeamDetails = async () => {
        setLoading(true);
        try {
            const response = await fetch(`http://localhost:8000/user/${sportType}/${teamName}/?gender=mens&level=college`);
            if (!response.ok) {
                throw new Error(`${response.status} (HTTP not found)`);
            }
            const data = await response.json();
            console.log("Fetched team data:", data); // Logging the full response

            // Check if there are teams available and set the first one
            if (data.data && data.data.teams && data.data.teams.length > 0) {
                setTeamData(data.data.teams[0]); // Get the first team object
            } else {
                throw new Error('No team data available.');
            }
        } catch (err) {
            console.error(err);
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchTeamDetails();
    }, [sportType, teamName]);

    if (loading) return <p>Loading...</p>;
    if (error) return <p>Error: {error}</p>;
    if (!teamData) return <p>No team data available.</p>;

    return (
        <div>
            <h2>{teamData.team_name} Details</h2>
            <h3>Recent Opponents</h3>
            {teamData.recent_opp && teamData.recent_opp.length > 0 ? (
                <ul>
                    {teamData.recent_opp.map((opponentId, index) => (
                        <li key={index}>Opponent ID: {opponentId}</li>
                    ))}
                </ul>
            ) : (
                <p>No opponents found for this season.</p>
            )}
        </div>
    );
};

export default TeamDetails;
