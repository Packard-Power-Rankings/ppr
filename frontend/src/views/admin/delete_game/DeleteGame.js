import React, { useEffect, useState } from "react";
import {
    CContainer,
    CRow,
    CCol,
    CButton
} from "@coreui/react";
import Select from "react-select";
import api from "src/api";
import { useSelector } from "react-redux";


const DeleteGame = () => {
    // Need to get team names along with game date.
    // Will need to have both teams input into search then date
    // will populate off of one of the teams season_opp array
    // then a selectable date will be available.
    const sport = useSelector((state) => state.sport);
    const gender = useSelector((state) => state.gender);
    const level = useSelector((state) => state.level);
    const [ teamsOptions, setTeamsOptions ] = useState([]);
    const [ loading, setLoading ] = useState(false);
    const [ teamOne, setTeamOne ] = useState(null);
    const [ teamTwo, setTeamTwo ] = useState(null);
    const [ gameData, setGameData ] = useState([]);
    const [ gameDate, setGameDate ] = useState(null);
    const [ gameWaiting, setGameWaiting ] = useState(false);

    const handleGameDelete = async () => {
        // Game deletion needs the two teams id's and the game id then will delete from
        // database
        const encodedDate = encodeURIComponent(`${gameDate.value}`);
        try {
            const response = await api.delete(
                `/delete-game/${teamOne.value}/${teamTwo.value}/${encodedDate}/?sport_type=${sport}&gender=${gender}&level=${level}`,
                {
                    headers: {"Content-Type": "application/json"},
                    withCredentials: true
                }
            );
            console.log(response);
        } catch (error) {
            console.error("Failed to delete game", error)
        }
    }

    const handleGameDate = async () => {
        try {
            setGameWaiting(true);
            const response = await api.get(
                `/season-dates/${teamOne.value}/${teamTwo.value}/?sport_type=${sport}&gender=${gender}&level=${level}`,
                {
                    headers: {"Content-Type": "application/json"},
                    withCredentials: true
                }
            );
            setGameData(response.data.map(item => ({
                value: item.game_id,
                label: item.game_date
            })))
        } catch (error) {
            console.error("Failed to fetch game dates", error);
        } finally {
            setGameWaiting(false);
        }
    }

    const handleTeamsOptions = async () => {
        try {
            setLoading(true);
            const response = await api.get(
                `/teams-ids/?sport_type=${sport}&gender=${gender}&level=${level}`,
                {
                    headers: {"Content-Type": 'application/json'},
                    withCredentials: true
                }
            )
            const teamsArray = response.data.data.teams
            setTeamsOptions(teamsArray.map(item => ({
                value: item.team_id,
                label: item.team_name
            })));
        } catch (error) {
            console.log("Error occured when trying to fetch team names and ids", error);
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        handleTeamsOptions()
    }, [])

    return (
        <>
            <CContainer>
                <CRow>
                    <CCol>
                        <Select options={teamsOptions} placeholder="Select Team 1"
                            isSearchable isDisabled={loading} value={teamOne} onChange={setTeamOne} />
                    </CCol>
                    <CCol>
                        <Select options={teamsOptions} placeholder="Select Team 2"
                            isSearchable isDisabled={loading} value={teamTwo} onChange={setTeamTwo} />
                    </CCol>
                    <CCol>
                        <CButton as="input" type="button" color="primary" value="Get Dates" onClick={handleGameDate}/>
                    </CCol>
                </CRow>
                <CRow>
                    <CCol>
                        <Select options={gameData} placeholder="Select Date"
                            isSearchable isDisabled={gameWaiting} value={gameDate} onChange={setGameDate} />
                    </CCol>
                    <CCol>
                        <CButton as="input" type="button" color="danger" value="Delete Game" onClick={handleGameDelete}/>
                    </CCol>
                </CRow>
            </CContainer>
        </>
    )
}

export default DeleteGame