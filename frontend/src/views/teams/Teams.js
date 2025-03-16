import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import api from "src/api";
import {
    CTable,
    CTableHead,
    CTableRow,
    CTableHeaderCell,
    CTableDataCell,
    CTableBody,
    CSpinner,
} from '@coreui/react'

const Teams = () => {
    const { sport, gender, level } = useParams();
    const [teams, setTeams] = useState([]);
    const [loading, setLoading] = useState([]);
    const [error, setError] = useState([]);

    const getLatestPowerRanking = (powerRanking) => {
        if (!powerRanking || powerRanking.length === 0) return '-';

        const rankingObj = powerRanking[0];
        
        const dates = Object.keys(rankingObj);
        const latestDate = dates[0];

        return parseFloat(rankingObj[latestDate]).toFixed(2);
    };

    const fetchTeams = async () => {
        try {
            setLoading(true);

            const teamsData = await api.get(
                `/teams/?sport_type=${sport}&gender=${gender}&level=${level}`
            );

            setTeams(teamsData.data.data.teams);
            setError(null);
        } catch (error) {
            console.log("Error fetching teams data", error);
            setError("Failed To Get Teams Data");
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        fetchTeams();
    }, [sport, gender, level])

    if (loading) {
        return (
            <div className="d-flex justify-content-center p-4">
                <CSpinner />
            </div>
        );
    }

    if (error) {
        return <div className="text-danger p-3">{error}</div>;
    }

    return (
        <div>
            <CTable>
                <CTableHead color="light" style={{ position: 'sticky', top: 114, zIndex: 1 }}>
                    <CTableRow>
                        <CTableHeaderCell scope="col">Rank</CTableHeaderCell>
                        <CTableHeaderCell scope="col">Team</CTableHeaderCell>
                        <CTableHeaderCell scope="col">Power</CTableHeaderCell>
                        <CTableHeaderCell scope="col">Div. Rank</CTableHeaderCell>
                        <CTableHeaderCell scope="col">Div.</CTableHeaderCell>
                        <CTableHeaderCell scope="col">W</CTableHeaderCell>
                        <CTableHeaderCell scope="col">L</CTableHeaderCell>
                    </CTableRow>
                </CTableHead>
                <CTableBody>
                    {teams.map((team) => (
                        <CTableRow>
                            <CTableDataCell>{team.overall_rank}</CTableDataCell>
                            <CTableDataCell>
                                <Link to={`/team/${encodeURIComponent(team.team_name)}/${sport}/${gender}/${level}`}>
                                    {team.team_name}
                                </Link>
                            </CTableDataCell>
                            <CTableDataCell>{getLatestPowerRanking(team.power_ranking)}</CTableDataCell>
                            <CTableDataCell>{team.division_rank}</CTableDataCell>
                            <CTableDataCell>{team.division}</CTableDataCell>
                            <CTableDataCell>{team.wins}</CTableDataCell>
                            <CTableDataCell>{team.losses}</CTableDataCell>
                        </CTableRow>
                    ))}
                </CTableBody>
            </CTable>
        </div>
    )
}

export default Teams