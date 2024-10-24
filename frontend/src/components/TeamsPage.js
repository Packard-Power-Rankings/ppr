import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';

const TeamsPage = () => {
    const { sportType } = useParams(); // Get sportType from the URL
    const [teams, setTeams] = useState([]);
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(true);

    const fetchTeams = async () => {
        setLoading(true);
        try {
            const response = await fetch(`http://localhost:8000/${sportType}/?gender=mens&level=college`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            if (data.data && Array.isArray(data.data.data)) {
                setTeams(data.data.data);
            } else {
                throw new Error('Expected an array of teams');
            }
        } catch (err) {
            console.error(err);
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchTeams(); // Fetch teams when the component mounts
    }, [sportType]);

    if (loading) return <p>Loading...</p>;
    if (error) return <p>Error: {error}</p>;

    return (
        <div>
            <h2>{sportType.charAt(0).toUpperCase() + sportType.slice(1)} Teams</h2>
            <div className="team-list">
                {teams.map(team => (
                    <div key={team.team_id} className="team-info">
                        <p>{team.team_name}</p>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default TeamsPage;
