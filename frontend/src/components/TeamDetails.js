import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';

const TeamDetails = () => {
    const { teamId } = useParams(); // Get teamId from the URL
    const [team, setTeam] = useState(null);
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(true);

    const fetchTeamDetails = async () => {
        setLoading(true);
        try {
            const response = await fetch(`http://localhost:8000/team/${teamId}`); // Adjust the endpoint as needed
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            setTeam(data); // Assuming the data contains team information directly
        } catch (err) {
            console.error(err);
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchTeamDetails(); // Fetch team details when the component mounts
    }, [teamId]);

    if (loading) return <p>Loading...</p>; // Display loading message
    if (error) return <p>Error: {error}</p>; // Handle error

    return (
        <div>
            <h2>{team?.team_name} Details</h2>
            {/* Display team details here */}
            <p>{team?.description}</p> {/* Adjust according to your data structure */}
            {/* Add more team information as needed */}
        </div>
    );
};

export default TeamDetails;
