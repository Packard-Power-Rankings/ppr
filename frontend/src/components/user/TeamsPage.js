import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import './TeamsPage.css';

const TeamsPage = () => {
    const { sportType } = useParams();
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
            if (data.data && Array.isArray(data.data.teams)) {
                setTeams(data.data.teams);
            } else {
                setTeams([]); // No teams found
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
        fetchTeams();
    }, [sportType]);

    if (loading) return <p>Loading...</p>;
    if (error) return <p>Error: {error}</p>;

    return (
        <div>
            <h2>{sportType.charAt(0).toUpperCase() + sportType.slice(1)} Teams</h2>
            <div className="team-table">
                <div className="table-header">
                    <span>Overall Rank</span>
                    <span>Team Name</span>
                    <span>Power Ranking</span>
                    <span>Division Rank</span>
                    <span>Division</span>
                    <span>Win/Loss</span>
                </div>
                {teams.map(team => (
                    <Link
                        to={`/user/${sportType}/${team.team_name}`}
                        key={team.team_id}
                        className="team-row"
                    >
                        <span>{team.overall_rank ?? 'N/A'}</span>
                        <span>{team.team_name}</span>
                        <span>{team.power_ranking?.[0]?.toFixed(2) ?? 'N/A'}</span>
                        <span>{team.division_rank ?? 'N/A'}</span>
                        <span>{team.division ?? 'N/A'}</span>
                        <span>{team.wins} / {team.losses}</span>
                    </Link>
                ))}
            </div>
        </div>
    );
};

export default TeamsPage;
