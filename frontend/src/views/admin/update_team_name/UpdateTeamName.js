import React, { useState, useEffect } from "react";
import {
    CForm,
    CFormText,
    CFormInput,
    CRow,
    CCol,
    CButton,
    CModal,
    CModalHeader,
    CModalTitle,
    CModalBody,
    CModalFooter
} from "@coreui/react";
import { useSelector } from "react-redux";
import Select from "react-select";
import api from "src/api";

const UpdateNames = () => {
    const sport = useSelector((state) => state.sport);
    const gender = useSelector((state) => state.gender);
    const level = useSelector((state) => state.level);
    const [ newTeamName, setTeamName ] = useState('');
    const [ oldTeamName, setOldNames ] = useState([]);
    const [ team, setTeam ] = useState(null);
    const [ teamsOptions, setTeamsOptions ] = useState([]);
    const [ filePopUp, setFilePopUp ] = useState(false);

    const handleUpdateTeamName = async () => {
        console.log(`team id ${oldTeamName.value}`)
        try {
            const response = await api.put(
                `/update-name/${oldTeamName.value}/${newTeamName}/?sport_type=${sport}&gender=${gender}&level=${level}`,
                {},
                {
                    headers: {"Content-Type": 'application/json'},
                    withCredentials: true
                }
            )
            setFilePopUp(true);
            console.log(response);
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

    useEffect(() => {
        handleTeamNameIds();
    }, []);

    return (
        <div>
            <CForm>
                <CRow>
                    <CCol>
                        <b>Current Team Name</b>
                        <Select 
                            options={teamsOptions}
                            label='Select Team'
                            placeholder="Select team..."
                            isSearchable value={oldTeamName}
                            onChange={setOldNames}
                        />
                    </CCol>
                    <CCol>
                        <b>New Team Name</b>
                        <CFormInput
                            type="text"
                            placeholder = "Enter new name..."
                            value={newTeamName}
                            onChange={(e) => setTeamName(e.target.value)}
                        />
                        <br/>
                        <CButton as="input" type="button" color="primary" value="Update Team Name" onClick={handleUpdateTeamName}/>
                    </CCol>
                </CRow>
            </CForm>
            <CModal visible={filePopUp} onClose={() => setFilePopUp(false)}>
                <CModalHeader>
                    <CModalTitle>Notification</CModalTitle>
                </CModalHeader>
                <CModalBody>
                    <b>{oldTeamName}</b> changed to <b>{newTeamName}</b>
                </CModalBody>
                <CModalFooter>
                    <button className="btn btn-primary" onClick={() => setFilePopUp(false)}>
                        OK
                    </button>
                </CModalFooter>
            </CModal>
        </div>
    )
}

export default UpdateNames
