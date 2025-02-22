import React, { useEffect } from "react";
import {
    CSpinner,
    CContainer,
    CRow,
    CCol,
    CCard,
    CCardBody,
    CCardHeader,
    CTable,
    CTableHead,
    CTableRow,
    CTableHeaderCell,
    CTableDataCell,
    CTableBody,
} from "@coreui/react";
import { useParams } from "react-router-dom";
import { useState } from "react";
import api from "src/api";

const Team = () => {
    const { team_name, sport, gender, level } = useParams();
    const [ team, setTeam ] = useState({});
    const [ seasonOpp, setOpp ] = useState([])
    const [ loading, setLoading ] = useState(false);
    const [ error, setError ] = useState(null);

    const getLatestPowerRanking = (powerRanking) => {
        if (!powerRanking || powerRanking.length === 0) return '-';

        const rankingObj = powerRanking[0];

        const dates = Object.keys(rankingObj);
        const latestDate = dates[0];

        return rankingObj[latestDate].toFixed(2);
    };

    const fetchTeamInfo = async () => {
        try {
            setLoading(true);
            setError(null);

            const teamInfo = await api.get(`teams/${team_name}/?sport_type=${sport}&gender=${gender}&level=${level}`);
            // console.log(teamInfo.data.data.teams.season_opp);
            setTeam(teamInfo.data.data.teams);
            setOpp(teamInfo.data.data.teams.season_opp);
        } catch (error) {
            setError(`Error in Retrieving ${team_name} Information`)
        } finally {
            setLoading(false);
        }

    }

    useEffect(() => {
        fetchTeamInfo();
    }, [team_name, sport, gender, level])

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
            <CContainer fluid className="p-4">
                <CCard>
                    <CCardHeader>
                        <h3>{team_name}</h3>
                        <h6>Rank: {team.overall_rank}</h6>
                    </CCardHeader>
                    <CCardBody>
                        <CRow>
                            <CCol md="6">
                                <h6>Division: {team.division}</h6>
                                <h6>Conference: {team.conference}</h6>
                                <h6>Division Rank: {team.division_rank}</h6>
                            </CCol>
                            <CCol md="6">
                                <h6>Power Rank: {getLatestPowerRanking(team.power_ranking)}</h6>
                                <h6>Wins: {team.wins}</h6>
                                <h6>Losses: {team.losses}</h6>
                            </CCol>
                        </CRow>
                    </CCardBody>
                </CCard>
            </CContainer>
            <CTable align="middle" hover responsive>
                <CTableHead>
                    <CTableRow>
                        <CTableHeaderCell className="py-3">Upload Date</CTableHeaderCell>
                        <CTableHeaderCell className="py-3">Opponent</CTableHeaderCell>
                        <CTableHeaderCell className="text-center py-3">Home Game</CTableHeaderCell>
                        <CTableHeaderCell className="text-center py-3">Home Score</CTableHeaderCell>
                        <CTableHeaderCell className="text-center py-3">Home z-score</CTableHeaderCell>
                        <CTableHeaderCell className="text-center py-3">Away Score</CTableHeaderCell>
                        <CTableHeaderCell className="text-center py-3">Away z-score</CTableHeaderCell>
                        <CTableHeaderCell className="text-center py-3">Result</CTableHeaderCell>
                    </CTableRow>
                </CTableHead>
                <CTableBody>
                    {seasonOpp.map((game, index) => (
                        <CTableRow key={index}>
                            <CTableDataCell className="py-3">{game.game_date}</CTableDataCell>
                            <CTableDataCell>{game.opponent_name}</CTableDataCell>
                            <CTableDataCell className="text-center">
                                {game.home_team ? 'Yes' : 'No'}
                            </CTableDataCell>
                            <CTableDataCell className="text-center">{game.home_score}</CTableDataCell>
                            <CTableDataCell className="text-center">{game.home_z_score.toFixed(2)}</CTableDataCell>
                            <CTableDataCell className="text-center">{game.away_score}</CTableDataCell>
                            <CTableDataCell className="text-center">{game.away_z_score.toFixed(2)}</CTableDataCell>
                            <CTableDataCell className="text-center">
                                {game.home_score > game.away_score
                                    ? 'Win'
                                    : game.home_score < game.away_score
                                    ? 'Loss'
                                    : 'Draw'}
                            </CTableDataCell>
                        </CTableRow>
                    ))}
                </CTableBody>
            </CTable>
        </div>
    )
}

export default Team