import React from "react";
import Select from "react-select";
import { 
    CButton,
    CForm,
    CCol,
    CFormCheck,
    CFormSelect,
    CTable,
    CTableHead,
    CTableRow,
    CTableHeaderCell,
    CTableDataCell,
    CTableBody,
    CCard,
    CCardBody,
    CCardHeader,
    CRow
 } from "@coreui/react";
 import { useState, useEffect } from "react";
import api from "src/api";


const Predictions = () => {
    const [ sport, setSport ] = useState('football');
    const [ gender, setGender ] = useState('mens');
    const [ level, setLevel ] = useState('high_school');
    const [ loading, setLoading ] = useState(false);
    const [ teamsOptions, setTeamsOptions ] = useState([]);
    const [ teamOne, setTeamOne ] = useState(null);
    const [ teamTwo, setTeamTwo ] = useState(null);
    const [ homeFieldAdv, setFieldAdv ] = useState(true);
    const [ predValues, setValues ] = useState([]);

    useEffect(() => {
        const debounceFetch = setTimeout(async () => {
            setLoading(true);
            try {
                const teamNames = await api.get(`/predictions/?sport_type=${sport}&gender=${gender}&level=${level}`);
                setTeamsOptions(teamNames.data.data.teams.map(item => ({
                    value: item.team_name,
                    label: item.team_name
                })));
            } catch (error) {
                console.log("Error fetching teams data", error);
            } finally {
                setLoading(false);
            }
        }, 500)
        return () => clearTimeout(debounceFetch);
    }, [sport, gender, level])

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!teamOne || !teamTwo) {
            alert("Please make a selection for both teams");
            return;
        }

        try {
            const response = await api.get(
                `/predictions/${teamOne.value}/${teamTwo.value}/${homeFieldAdv}/?sport_type=${sport}&gender=${gender}&level=${level}`
            );
            // console.log(response);
            setValues([
                { team: teamOne.value, score: response.data[teamOne.value].toFixed(2) },
                { team: teamTwo.value, score: response.data[teamTwo.value].toFixed(2) }
            ]);
        } catch (error) {
            console.log("Error fetching teams data", error);
        }
    }

    return (
        <CCard className="p-3">
            <CCardHeader>
                <h4>Game Prediction Form</h4>
            </CCardHeader>
            <CCardBody>
                <CForm onSubmit={handleSubmit}>
                    <CRow className="mb-3">
                        <CCol sm={3}><label htmlFor="sportType"><strong>Sport:</strong></label></CCol>
                        <CCol sm={6}>
                            <CFormSelect id="sportType" value={sport} onChange={(event) => setSport(event.target.value)}>
                                <option value="football">Football</option>
                                <option value="basketball">Basketball</option>
                            </CFormSelect>
                        </CCol>
                    </CRow>

                    <CRow className="mb-3">
                        <CCol sm={3}><label htmlFor="genderType"><strong>Gender:</strong></label></CCol>
                        <CCol sm={6}>
                            <CFormSelect id="genderType" value={gender} onChange={(event) => setGender(event.target.value)}>
                                <option value="mens">Mens</option>
                                <option value="womens">Womens</option>
                            </CFormSelect>
                        </CCol>
                    </CRow>

                    <CRow className="mb-3">
                        <CCol sm={3}><label htmlFor="levelType"><strong>Level:</strong></label></CCol>
                        <CCol sm={6}>
                            <CFormSelect id="levelType" value={level} onChange={(event) => setLevel(event.target.value)}>
                                <option value="high_school">High School</option>
                                <option value="college">College</option>
                            </CFormSelect>
                        </CCol>
                    </CRow>

                    <CRow className="mb-3">
                        <CCol sm={3}><strong>Home field:</strong></CCol>
                        <CCol sm={6}>
                            <CFormCheck type="checkbox" name="hfa" id="hfaSelection" label="Apply home-field advantage to Team 1 (home team)"
                                checked={homeFieldAdv} onChange={() => setFieldAdv(prev => !prev)} />
                        </CCol>
                    </CRow>
                    <CRow className="mb-3">
                        <CCol sm={3}><strong>Team 1:</strong></CCol>
                        <CCol sm={6}>
                            <Select options={teamsOptions} classNamePrefix="react-select" placeholder="Select Team 1"
                                isSearchable isClearable isDisabled={loading} value={teamOne} onChange={setTeamOne} />
                        </CCol>
                    </CRow>

                    <CRow className="mb-3">
                        <CCol sm={3}><strong>Team 2:</strong></CCol>
                        <CCol sm={6}>
                            <Select options={teamsOptions} classNamePrefix="react-select" placeholder="Select Team 2"
                                isSearchable isClearable isDisabled={loading} value={teamTwo} onChange={setTeamTwo} />
                        </CCol>
                    </CRow>

                    <CRow className="text-center mt-4">
                        <CCol>
                            <CButton type="submit" color="primary" variant="outline">Submit</CButton>
                        </CCol>
                    </CRow>
                </CForm>

                {predValues.length > 0 && (
                    <CCard className="mt-4">
                        <CCardHeader>
                            <h5>Predicted Scores</h5>
                        </CCardHeader>
                        <CCardBody>
                            <CTable bordered hover responsive>
                                <CTableHead color="dark">
                                    <CTableRow>
                                        <CTableHeaderCell>Team</CTableHeaderCell>
                                        <CTableHeaderCell>Score</CTableHeaderCell>
                                    </CTableRow>
                                </CTableHead>
                                <CTableBody>
                                    {predValues.map(({ team, score }) => (
                                        <CTableRow key={team} className={score === Math.max(...predValues.map(t => t.score)) ? "table-success" : ""}>
                                            <CTableDataCell><strong>{team}</strong></CTableDataCell>
                                            <CTableDataCell>{score}</CTableDataCell>
                                        </CTableRow>
                                    ))}
                                </CTableBody>
                            </CTable>
                        </CCardBody>
                    </CCard>
                )}
            </CCardBody>
        </CCard>
    )
}

export default Predictions