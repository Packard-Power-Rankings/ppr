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


const DeleteTeam = () => {
    const sport = useSelector((state) => state.sport);
    const gender = useSelector((state) => state.gender);
    const level = useSelector((state) => state.level);
    const [ team, setTeam ] = useState(nul);
    const [ teamsOptions, setTeamsOptions ] = useState([]);

    const handleTeamDelete = async () => {
        try {
            const response = await api.delete(
                `/delete-team/${team.label}/${team.value}/?sport_type=${sport}&gender=${gender}&level=${level}`,
                {
                    headers: {"Content-Type": 'application/json'},
                    withCredentials: true
                }
            )
            console.log(response);
        } catch (error) {
            console.error("Error when trying to delete team from database", error);
        }
    }

    const handleTeamNameIds = async () => {
        try {
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
            console.error("Failed to retrieve team names and ids", error);
        }
    }

    useEffect(() => {
        handleTeamNameIds();
    }, []);

    return (
        <>
            <CContainer>
                <CRow>
                    <CCol>
                        <Select options={teamsOptions} placeholder="Select Team"
                            isSearchable isDisabled={loading} value={team} onChange={setTeam} />
                    </CCol>
                    <CCol>
                        <CButton as="input" type="button" color="danger" value="Delete Game" onClick={handleTeamDelete}/>
                    </CCol>
                </CRow>
            </CContainer>
        </>
    )
}

export default DeleteTeam