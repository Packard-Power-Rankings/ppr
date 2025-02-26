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