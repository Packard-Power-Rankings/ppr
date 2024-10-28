import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import './TeamsPage.css'; // Import the CSS file for styling

const TeamsPage = () => {
    const { sportType } = useParams(); // Get sportType from the URL
    const [teams, setTeams] = useState([]);
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(true);

    const fetchTeams = async () => {
        setLoading(true);
        try {
            const response = await fetch(`http://localhost:8000/user/${sportType}/?gender=mens&level=college`);
            if (!response.ok) {
                throw new Error(`${response.status} (HTTP not found)`);
            }

            const data = await response.json();
            console.log("Fetched data:", data); // Log the data to check its structure

            // Access teams from `data.data` and set state
            if (Array.isArray(data.data)) {
                setTeams(data.data);
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

    if (loading) return null; // Hide the loading message
    if (error) return <>{error}</>;

    return (
        <div className="team-list">
            {teams.map(team => (
                <Link 
                    to={`/user/${sportType}/${team.team_name}`} 
                    key={team.team_id} 
                    className="team-link"
                >
                    <div className="team-row">
                        <p className="team-name">{team.team_name}</p>
                        <div className="team-details">
                            <span><strong>Overall Rank:</strong> {team.overall_rank}</span>
                            <span><strong>Power:</strong> {team.power_ranking ? team.power_ranking[0] : 'N/A'}</span>
                            <span><strong>Division Rank:</strong> {team.division_rank}</span>
                            <span><strong>Division:</strong> {team.division}</span>
                            <span><strong>Wins/Losses:</strong> {team.wins} / {team.losses}</span>
                        </div>
                    </div>
                </Link>
            ))}
        </div>
    );
};

export default TeamsPage;
