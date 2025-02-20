import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import api from "src/api";
import {
    CTable,
    CTableHead,
    CTableRow,
    CTableHeaderCell,
    CTableDataCell,
    CTableBody,
    CSpinner,
    CNavLink
} from '@coreui/react'

const Teams = () => {
    const { sport, gender, level } = useParams();
    const [teams, setTeams] = useState([]);
    const [loading, setLoading] = useState([]);
    const [error, setError] = useState([]);

    const getLatestPowerRanking = (powerRanking) => {
        if (!powerRanking || powerRanking.length === 0) return '-';
        
        // Get the first (and only) object from the array
        const rankingObj = powerRanking[0];
        
        // Get all dates and find the latest one
        const dates = Object.keys(rankingObj);
        const latestDate = dates[0]; // Since there's only one date
        
        // Return the power ranking value formatted to 2 decimal places
        return rankingObj[latestDate].toFixed(2);
      };

    const fetchTeams = async () => {
        try {
            setLoading(true);

            const teamsData = await api.get(`/${sport}/${gender}/${level}`);
            // console.log(teamsData.data.data.teams);

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
                            <CTableDataCell>{team.team_name}</CTableDataCell>
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