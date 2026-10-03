import React, { useCallback, useEffect } from "react";
import {
    CAlert,
    CButton,
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
    CFormLabel,
    CFormTextarea,
    CModal,
    CModalTitle,
    CModalBody,
    CModalHeader,
    CModalFooter
} from "@coreui/react";
import CIcon from '@coreui/icons-react';
import { cilFlagAlt } from '@coreui/icons';
import { Link, useParams } from "react-router-dom";
import { useState } from "react";
import api from "src/api";

const Team = () => {
    const { team_name, sport, gender, level } = useParams();
    const [ team, setTeam ] = useState({});
    const [ seasonOpp, setOpp ] = useState([])
    const [ loading, setLoading ] = useState(false);
    const [ error, setError ] = useState(null);
    const [ reportGame, setReportGame ] = useState(null);
    const [ issueDescription, setIssueDescription ] = useState('');
    const [ reportError, setReportError ] = useState('');
    const [ reporting, setReporting ] = useState(false);
    const [ notification, setNotification ] = useState('');

    const getLatestPowerRanking = (powerRanking) => {
        if (!powerRanking || powerRanking.length === 0) return '-';

        const rankingObj = powerRanking[0];

        const dates = Object.keys(rankingObj);
        const latestDate = dates[0];

        return rankingObj[latestDate].toFixed(2);
    };

    const fetchTeamInfo = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);

            const teamInfo = await api.get(`teams/${encodeURIComponent(team_name)}/`, {
                params: { sport_type: sport, gender, level },
            });
            setTeam(teamInfo.data.data.teams);
            setOpp([...teamInfo.data.data.teams.season_opp].sort((firstGame, secondGame) =>
                (secondGame.game_date || '').localeCompare(firstGame.game_date || '')
            ));
        } catch (error) {
            setError(`Error in Retrieving ${team_name} Information`)
        } finally {
            setLoading(false);
        }

    }, [gender, level, sport, team_name])

    const openFlagDialog = async (game) => {
        try {
            const checkIfFlagged = await api.get(
                `/check-flagged/${encodeURIComponent(game.game_id)}?sport_type=${sport}&gender=${gender}&level=${level}`,
                {
                    headers: {"Content-Type": "application/json"}
                }
            )
            if (checkIfFlagged.data.game_flagged) {
                setNotification(checkIfFlagged.data.message);
                return;
            }
            setIssueDescription('');
            setReportError('');
            setReportGame(game);
        } catch (error) {
            setNotification(
                error.response?.data?.detail || 'The game could not be checked for an existing report.'
            );
        }
    }

    const submitFlaggedGame = async () => {
        if (!reportGame || issueDescription.trim().length < 5) return;
        setReporting(true);
        setReportError('');
        try {
            const storeFlaggedGame = await api.post(
                `/flagged-game/?sport_type=${sport}&gender=${gender}&level=${level}`,
                {
                    game_id: reportGame.game_id,
                    team1_id: team.team_id,
                    team1_name: team_name,
                    team2_id: reportGame.opponent_id,
                    team2_name: reportGame.opponent_name,
                    description: issueDescription.trim(),
                },
                {
                    headers: {"Content-Type": "application/json"}
                }
            )
            if (storeFlaggedGame.data.game_flagged) {
                setReportGame(null);
                setNotification(storeFlaggedGame.data.message);
                window.dispatchEvent(new Event('flagged-issues-changed'));
            }
        } catch (error) {
            const detail = error.response?.data?.detail;
            setReportError(
                typeof detail === 'string' ? detail : 'The game issue could not be reported.'
            );
        } finally {
            setReporting(false);
        }
    }

    useEffect(() => {
        fetchTeamInfo();
    }, [fetchTeamInfo])

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

    const shortName = team.short_name || team.team_name || team_name;
    const displayName = team.long_name && team.long_name !== shortName
        ? `${shortName} - ${team.long_name}`
        : shortName;

    return (
        <div>
            <CContainer fluid className="p-4">
                <CCard>
                    <CCardHeader>
                        <h3>{displayName}</h3>
                        <CRow className="g-2">
                            <CCol xs="6">
                                <h6 className="mb-0">Rank: {team.overall_rank ?? '-'}</h6>
                            </CCol>
                            <CCol xs="6">
                                <h6 className="mb-0">Power: {getLatestPowerRanking(team.power_ranking)}</h6>
                            </CCol>
                        </CRow>
                        <CRow className="g-2 mt-1">
                            <CCol xs="6">
                                <h6 className="mb-0">Division Rank: {team.division_rank ?? '-'}</h6>
                            </CCol>
                            <CCol xs="6">
                                <h6 className="mb-0">Conference Rank: {team.conference_rank ?? '-'}</h6>
                            </CCol>
                        </CRow>
                    </CCardHeader>
                    <CCardBody>
                        <CRow>
                            <CCol md="6">
                                <h6>ID: {team.team_id ?? '-'}</h6>
                                <h6>State: {team.state || '-'}</h6>
                                <h6>Division: {team.division}</h6>
                                <h6>Conference: {team.conference}</h6>
                            </CCol>
                            <CCol md="6">
                                <h6>Last Rank: {team.last_rank ?? '-'}</h6>
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
                    {seasonOpp.map((game, index) => {
                        const teamScore = game.home_team ? game.home_score : game.away_score
                        const opponentScore = game.home_team ? game.away_score : game.home_score
                        const result = teamScore > opponentScore
                            ? 'Win'
                            : teamScore < opponentScore
                                ? 'Loss'
                                : 'Draw'
                        const resultClass = result === 'Win'
                            ? 'table-success'
                            : result === 'Loss'
                                ? 'table-danger'
                                : ''

                        return (
                        <CTableRow key={index} className={resultClass}>
                            <CTableDataCell className="py-3">{game.game_date}</CTableDataCell>
                            <CTableDataCell>
                                <Link to={`/team/${encodeURIComponent(game.opponent_name)}/${sport}/${gender}/${level}`}>
                                    {game.opponent_name}
                                </Link>
                            </CTableDataCell>
                            <CTableDataCell className="text-center">
                                {game.home_team ? 'Yes' : 'No'}
                            </CTableDataCell>
                            <CTableDataCell className="text-center">{game.home_score}</CTableDataCell>
                            <CTableDataCell className="text-center">{game.home_z_score.toFixed(2)}</CTableDataCell>
                            <CTableDataCell className="text-center">{game.away_score}</CTableDataCell>
                            <CTableDataCell className="text-center">{game.away_z_score.toFixed(2)}</CTableDataCell>
                            <CTableDataCell className="text-center">
                                {result}
                            </CTableDataCell>
                            <CTableDataCell className="text-center py-3">
                                <CButton
                                    type="button"
                                    color="warning"
                                    variant="ghost"
                                    size="sm"
                                    title="Report a problem with this game"
                                    aria-label={`Report issue for game against ${game.opponent_name}`}
                                    onClick={() => openFlagDialog(game)}
                                >
                                    <CIcon icon={cilFlagAlt} />
                                </CButton>
                            </CTableDataCell>
                        </CTableRow>
                        )
                    })}
                </CTableBody>
            </CTable>
            <CModal
                visible={Boolean(reportGame)}
                onClose={() => !reporting && setReportGame(null)}
            >
                <CModalHeader>
                    <CModalTitle>Report Game Issue</CModalTitle>
                </CModalHeader>
                <CModalBody>
                    {reportGame && (
                        <p className="mb-3">
                            {team.team_name || team_name} vs {reportGame.opponent_name} on{' '}
                            {reportGame.game_date}
                        </p>
                    )}
                    {reportError && <CAlert color="danger">{reportError}</CAlert>}
                    <CFormLabel htmlFor="game-issue-description">
                        Describe the issue and include a source link for verification, if available
                    </CFormLabel>
                    <CFormTextarea
                        id="game-issue-description"
                        rows={5}
                        maxLength={1000}
                        value={issueDescription}
                        disabled={reporting}
                        onChange={(event) => setIssueDescription(event.target.value)}
                    />
                    <div className="small text-body-secondary mt-1 text-end">
                        {issueDescription.length}/1000
                    </div>
                </CModalBody>
                <CModalFooter>
                    <CButton
                        type="button"
                        color="secondary"
                        variant="outline"
                        disabled={reporting}
                        onClick={() => setReportGame(null)}
                    >
                        Cancel
                    </CButton>
                    <CButton
                        type="button"
                        color="warning"
                        disabled={reporting || issueDescription.trim().length < 5}
                        onClick={submitFlaggedGame}
                    >
                        {reporting && <CSpinner className="me-2" size="sm" />}
                        Report Issue
                    </CButton>
                </CModalFooter>
            </CModal>
            <CModal visible={Boolean(notification)} onClose={() => setNotification('')}>
                <CModalHeader>
                    <CModalTitle>Notification</CModalTitle>
                </CModalHeader>
                <CModalBody>
                    {notification}
                </CModalBody>
                <CModalFooter>
                    <CButton color="primary" onClick={() => setNotification('')}>
                        OK
                    </CButton>
                </CModalFooter>
            </CModal>
        </div>
    )
}

export default Team
