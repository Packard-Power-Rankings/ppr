import React, { useEffect, useState } from "react";
import {
    CContainer,
    CRow,
    CCol,
    CButton,
    CSpinner
} from "@coreui/react";
import Select from "react-select";
import api from "src/api";
import { useSelector } from "react-redux";

const DeleteGame = () => {
    const sport = useSelector((state) => state.sport);
    const gender = useSelector((state) => state.gender);
    const level = useSelector((state) => state.level);

    const [teamsOptions, setTeamsOptions] = useState([]);
    const [loading, setLoading] = useState(false);
    const [teamOne, setTeamOne] = useState(null);
    const [teamTwo, setTeamTwo] = useState(null);
    const [gameData, setGameData] = useState([]);
    const [gameDate, setGameDate] = useState(null);
    const [gameWaiting, setGameWaiting] = useState(false);

    useEffect(() => {
        handleTeamsOptions();
    }, []);

    const handleTeamsOptions = async () => {
        try {
            setLoading(true);
            const response = await api.get(
                `/teams-ids/?sport_type=${sport}&gender=${gender}&level=${level}`,
                {
                    headers: { "Content-Type": "application/json" },
                    withCredentials: true
                }
            );
            const teamsArray = response.data.data.teams;
            setTeamsOptions(teamsArray.map(item => ({
                value: item.team_id,
                label: item.team_name
            })));
        } catch (error) {
            console.error("Error fetching team names and IDs:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleGameDate = async () => {
        if (!teamOne || !teamTwo) return;
        try {
            setGameWaiting(true);
            const response = await api.get(
                `/season-dates/${teamOne.value}/${teamTwo.value}/?sport_type=${sport}&gender=${gender}&level=${level}`,
                {
                    headers: { "Content-Type": "application/json" },
                    withCredentials: true
                }
            );
            setGameData(response.data.map(item => ({
                value: item.game_id,
                label: item.game_date
            })));
        } catch (error) {
            console.error("Failed to fetch game dates", error);
        } finally {
            setGameWaiting(false);
        }
    };

    const handleGameDelete = async () => {
        if (!teamOne || !teamTwo || !gameDate) return;
        try {
            const response = await api.delete(
                `/delete-game/${teamOne.value}/${teamTwo.value}/${encodeURIComponent(gameDate.value)}/${encodeURIComponent(gameDate.label)}/?sport_type=${sport}&gender=${gender}&level=${level}`,
                {
                    headers: { "Content-Type": "application/json" },
                    withCredentials: true
                }
            );
            console.log(response);
        } catch (error) {
            console.error("Failed to delete game", error);
        }
    };

    return (
        <CContainer className="mt-4">
            <CRow className="mb-3">
                <CCol>
                    <h4>Select Teams</h4>
                </CCol>
            </CRow>
            <CRow className="mb-3">
                <CCol>
                    <Select
                        options={teamsOptions}
                        placeholder="Select Team 1"
                        isSearchable
                        isClearable
                        isDisabled={loading}
                        value={teamOne}
                        onChange={(selected) => {
                            setTeamOne(selected);
                            setTeamTwo(null);
                        }}
                    />
                </CCol>
                <CCol>
                    <Select
                        options={teamsOptions.filter(team => team.value !== teamOne?.value)}
                        placeholder="Select Team 2"
                        isSearchable
                        isClearable
                        isDisabled={!teamOne || loading}
                        value={teamTwo}
                        onChange={setTeamTwo}
                    />
                </CCol>
                <CCol>
                    <CButton
                        color="primary"
                        disabled={!teamOne || !teamTwo}
                        onClick={handleGameDate}
                    >
                        {gameWaiting ? <CSpinner size="sm" /> : "Get Dates"}
                    </CButton>
                </CCol>
            </CRow>

            <CRow className="mb-3">
                <CCol>
                    <h4>Select Game Date</h4>
                </CCol>
            </CRow>
            <CRow className="mb-3">
                <CCol>
                    <Select
                        options={gameData}
                        placeholder="Select Date"
                        isSearchable
                        isClearable
                        isDisabled={gameWaiting || gameData.length === 0}
                        value={gameDate}
                        onChange={setGameDate}
                    />
                </CCol>
                <CCol>
                    <CButton
                        color="danger"
                        disabled={!gameDate}
                        onClick={handleGameDelete}
                    >
                        Delete Game
                    </CButton>
                </CCol>
            </CRow>
        </CContainer>
    );
};

export default DeleteGame;
