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
            const response = await fetch(`http://localhost:8000/user/${sportType}/${teamName}`);
            if (!response.ok) {
                throw new Error(`${response.status} (HTTP not found)`);
            }
            const data = await response.json();
            console.log("Fetched team data:", data);

            // Assuming data contains the team information including the season_opp array
            setTeamData(data); // Adjust based on the actual structure of the response
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
            <h2>{teamName} Details</h2>
            <p>Sport Type: {sportType}</p>
            <h3>Season Opponents</h3>
            {teamData.season_opp && teamData.season_opp.length > 0 ? (
                <ul>
                    {teamData.season_opp.map((opponent, index) => (
                        <li key={index}>Opponent ID: {opponent}</li> // Adjust based on your opponent data structure
                    ))}
                </ul>
            ) : (
                <p>No opponents found for this season.</p> // Message when the array is empty
            )}
        </div>
    );
};

export default TeamDetails;
