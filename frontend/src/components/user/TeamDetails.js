// src/components/user/TeamDetails.js
import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import './TeamDetails.css';

const TeamDetails = () => {
    const { sportType, gender, level, teamName } = useParams(); // Extract gender and level parameters
    const [teamData, setTeamData] = useState(null);
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(true);

    const fetchTeamDetails = async () => {
        setLoading(true);
        try {
            const response = await fetch(
                `http://localhost:8000/${sportType}/${teamName}/?gender=${gender}&level=${level}`
            );
            if (!response.ok) {
                throw new Error(`${response.status} (HTTP not found)`);
            }
            const data = await response.json();
            if (data.data && data.data.teams && data.data.teams.length > 0) {
                setTeamData(data.data.teams[0]);
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
    }, [sportType, teamName, gender, level]); // Update dependencies

    if (loading) return <p>Loading...</p>;
    if (error) return <p>Error: {error}</p>;
    if (!teamData) return <p>No team data available.</p>;

    return (
        <div>
            <h2>{teamData.team_name} Season Opponents</h2>
            <div className="team-table-container">
                <table className="team-table">
                    {/* Table Header */}
                    <thead>
                        <tr className="table-header">
                            <th>Game Date</th>
                            <th>Team Name</th>
                            <th>Score</th>
                            <th>Opponent</th>
                            <th>Home/Away</th>
                        </tr>
                    </thead>
                    <tbody>
                        {teamData.season_opp && teamData.season_opp.length > 0 ? (
                            teamData.season_opp.map((game, index) => (
                                <tr key={index} className="team-row">
                                    <td>{new Date(game.game_date).toLocaleDateString()}</td>
                                    <td>{teamData.team_name}</td>
                                    <td>{game.home_score} - {game.away_score}</td>
                                    <td>{game.opponent_name}</td>
                                    <td>{game.home_team === 1 ? 'Home' : 'Away'}</td>
                                </tr>
                            ))
                        ) : (
                            <tr><td colSpan="5">No season opponents available.</td></tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default TeamDetails;
