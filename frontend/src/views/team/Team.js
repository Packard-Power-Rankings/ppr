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
    CFormCheck,
    CModal,
    CModalTitle,
    CModalBody,
    CModalHeader,
    CModalFooter
} from "@coreui/react";
import { useParams } from "react-router-dom";
import { useState } from "react";
import api from "src/api";
import { legacy_createStore } from "redux";
import { check } from "prettier";

const Team = () => {
    const { team_name, sport, gender, level } = useParams();
    const [ team, setTeam ] = useState({});
    const [ seasonOpp, setOpp ] = useState([])
    const [ loading, setLoading ] = useState(false);
    const [ error, setError ] = useState(null);
    const [ gameFlagged, setGameFlagged ] = useState(false);
    const [ message, setMessage ] = useState('');

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

    const flagGame = async (index) => {
        console.log(team.team_id);
        console.log(seasonOpp[index].opponent_id);
        try {
            const checkIfFlagged = await api.get(
                `/check-flagged/${encodeURIComponent(seasonOpp[index].game_id)}?sport_type=${sport}&gender=${gender}&level=${level}`,
                {
                    headers: {"Content-Type": "application/json"},
                    withCredentials: false
                }
            )
            console.log(checkIfFlagged);
            if (checkIfFlagged.data.game_flagged) {
                setGameFlagged(true);
                setMessage(checkIfFlagged.data.message);
                return;
            } else {
                console.log(checkIfFlagged.data.message);
            }
            const storeFlaggedGame = await api.post(
                `/flagged-game/?sport_type=${sport}&gender=${gender}&level=${level}`,
                {
                    game_id: seasonOpp[index].game_id,
                    team1_id: team.team_id,
                    team1_name: team_name,
                    team2_id: seasonOpp[index].opponent_id,
                    team2_name: seasonOpp[index].opponent_name
                },
                {
                    headers: {"Content-Type": "application/json"},
                    withCredentials: false
                }
            )
            if (storeFlaggedGame.data.game_flagged) {
                setGameFlagged(true);
                setMessage(storeFlaggedGame.data.message);
            } else {
                console.log(storeFlaggedGame.data.message);
            }
        } catch (error) {
            console.log("Failed storing flagged game", error);
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
                        <CTableHeaderCell scope="col" className="py-3">Flag Game</CTableHeaderCell>
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
                            <CTableDataCell className="text-center py-3">
                                <CFormCheck id="checkboxNoLabel" disabled={gameFlagged} value="" aria-label="..." onClick={() => flagGame(index)}/>
                            </CTableDataCell>
                        </CTableRow>
                    ))}
                </CTableBody>
            </CTable>
            <CModal visible={gameFlagged} onClose={() => setGameFlagged(false)}>
                <CModalHeader>
                    <CModalTitle>Notification</CModalTitle>
                </CModalHeader>
                <CModalBody>
                    {message}
                </CModalBody>
                <CModalFooter>
                    <button className="btn btn-primary" onClick={() => setGameFlagged(false)}>
                        OK
                    </button>
                </CModalFooter>
            </CModal>
        </div>
    )
}

export default Team