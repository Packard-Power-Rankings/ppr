import React from "react";
import Select from "react-select";
import { 
    CButton,
    CForm,
    CCol,
    CFormCheck,
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
    const [ homeFieldAdv, setFieldAdv ] = useState(false);
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
                        <CCol sm={3}><strong>Sport:</strong></CCol>
                        <CCol sm={6}>
                            <CFormCheck inline type="radio" name="sportType" id="football" label="Football"
                                checked={sport === "football"} onChange={() => setSport("football")} />
                            <CFormCheck inline type="radio" name="sportType" id="basketball" label="Basketball"
                                checked={sport === "basketball"} onChange={() => setSport("basketball")} />
                        </CCol>
                    </CRow>

                    <CRow className="mb-3">
                        <CCol sm={3}><strong>Gender:</strong></CCol>
                        <CCol sm={6}>
                            <CFormCheck inline type="radio" name="genderType" id="mens" label="Mens"
                                checked={gender === "mens"} onChange={() => setGender("mens")} />
                            <CFormCheck inline type="radio" name="genderType" id="womens" label="Womens"
                                checked={gender === "womens"} onChange={() => setGender("womens")} />
                        </CCol>
                    </CRow>

                    <CRow className="mb-3">
                        <CCol sm={3}><strong>Level:</strong></CCol>
                        <CCol sm={6}>
                            <CFormCheck inline type="radio" name="levelType" id="high_school" label="High School"
                                checked={level === "high_school"} onChange={() => setLevel("high_school")} />
                            <CFormCheck inline type="radio" name="levelType" id="college" label="College"
                                checked={level === "college"} onChange={() => setLevel("college")} />
                        </CCol>
                    </CRow>

                    <CRow className="mb-3">
                        <CCol sm={3}><strong>Home Field Advantage:</strong></CCol>
                        <CCol sm={6}>
                            <CFormCheck type="checkbox" name="hfa" id="hfaSelection" label="Apply Home Field Advantage"
                                checked={homeFieldAdv} onChange={() => setFieldAdv(prev => !prev)} />
                        </CCol>
                    </CRow>
                    <CRow className="mb-3">
                        <CCol sm={3}><strong>Team 1:</strong></CCol>
                        <CCol sm={6}>
                            <Select options={teamsOptions} placeholder="Select Team 1"
                                isSearchable isClearable isDisabled={loading} value={teamOne} onChange={setTeamOne} />
                        </CCol>
                    </CRow>

                    <CRow className="mb-3">
                        <CCol sm={3}><strong>Team 2:</strong></CCol>
                        <CCol sm={6}>
                            <Select options={teamsOptions} placeholder="Select Team 2"
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