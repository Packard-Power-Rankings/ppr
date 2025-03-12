import React, { useState, useEffect } from "react";
import {
    CForm,
    CFormText,
    CFormInput,
    CRow,
    CCol
} from "@coreui/react";
import { useSelector } from "react-redux";
import Select from "src/views/forms/select/Select";

const UpdateNames = () => {
    const sport = useSelector((state) => state.sport);
    const gender = useSelector((state) => state.gender);
    const level = useSelector((state) => state.level);
    const [ newTeamName, setTeamName ] = useState('');
    const [ oldTeamName, setOldNames ] = useState([]);

    const handleUpdateTeamName = async (oldTeamName, newTeamName) => {
        try {
            const response = await put(
                `/update-name/${TeamsArray.get(item.team_name==oldTeamName).value}/${newTeamName}/?sport_type=${sport}&gender=${gender}&level=${level}`,
                {
                    headers: {"Content-Type": 'application/json'},
                    withCredentials: true
                }
            )
            console.log(response)
        }
        catch (error){
            console.log("Error when updating team name",error)
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

    return (
        <div>
            <CForm>
                <CRow>
                    <CCol>
                        <CFormInput
                            type="text"
                            label='New Team Name'
                            value={newTeamName}
                            onChange={() => setTeamName(newTeamName)}
                        />
                    </CCol>
                    <CCol>
                        <Select options={teamsOptions} placeholder="Select Team 1"
                            isSearchable isDisabled={loading} value={oldTeamName} onChange={setOldNames} />
                    </CCol>
                </CRow>
            </CForm>
        </div>
    )
}

export default UpdateNames