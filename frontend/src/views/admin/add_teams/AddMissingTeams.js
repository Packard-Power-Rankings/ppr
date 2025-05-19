import React, { useEffect, useState } from "react";
import { 
    CModal,
    CModalBody,
    CModalFooter,
    CModalHeader,
    CModalTitle,
    CTable,
    CTableBody,
    CTableHead,
    CTableHeaderCell,
    CTableDataCell,
    CTableRow,
    CFormInput
} from "@coreui/react";
import Select from "react-select";
import api from "src/api";
import { useSelector } from "react-redux";

const AddMissingTeams = ({ missingTeamNames, onClose }) => {
    const sport = useSelector((state) => state.sport);
    const gender = useSelector((state) => state.gender);
    const level = useSelector((state) => state.level);
    const [ isConference, setIsConference ] = useState(false);
    const [ conference, setConference ] = useState([]);
    const [ division, setDivision ] = useState([]);
    const [ states, setStates ] = useState([]);
    const [ formData, setFormData ] = useState([]);
    const [modalMessage, setModalMessage] = useState("");
    const [showMessageModal, setShowMessageModal] = useState(false);

    const handleInputChange = (index, field, value) => {
        console.log(value);
        setFormData((prevData) => {
            const newFormData = [...prevData];
            newFormData[index] = {...newFormData[index], [field]: value};
            return newFormData;
        });
    }


    const handleSubmit = async (e) => {
        // Add teams to database through backend endpoint
        e.preventDefault();
        try {
            const response = await api.post(
                `/add_teams/?sport_type=${sport}&gender=${gender}&level=${level}`,
                formData,
                {
                    headers: {"Content-Type": "application/json"},
                    withCredentials: true
                }
            );
            setModalMessage(response.data.message);
            setShowMessageModal(true);
        } catch (error) {
            console.log("Failed to add teams to database", error)
        }
    }


    const handleMissingTeams = async () => {
        // Get missing teams for selectable drop downs
        try {
            const response = await api.get(
                `/sports/?sport_type=${sport}&gender=${gender}&level=${level}`,
                {
                    headers: {
                        "Content-Type": "application/x-www-form-urlencoded"
                    },
                    withCredentials: true
                }
            )

            const response_items = response.data;
            setDivision(response_items.division.map(items => ({
                value: items.id,
                label: items.name
            })));
            setStates(response_items.states.map(items => ({
                value: items.id,
                label: items.name.state_code
            })));

            if (response_items.conference) {
                setIsConference(false);
                setConference(response_items.conference.map(items => ({
                    value: items.id,
                    label: items.name
                })));
            } else setIsConference(true);
            setFormData(missingTeamNames.map((team) => ({
                team_name: team,
                division: null,
                conference: null,
                power_ranking: "",
                state: null
            })));
        } catch (error) {
            console.log("Error retrieving sport information")
        }
    }


    useEffect(() => {
        handleMissingTeams();
    }, [])


    return (
        <>
            <CModal size="xl" backdrop="static" visible={true} onClose={onClose}>
                <CModalHeader>
                    <CModalTitle>Add Missing Teams</CModalTitle>
                </CModalHeader>
                <CModalBody>
                    <CTable>
                        <CTableHead>
                            <CTableRow>
                                <CTableHeaderCell scope="col">Team Name</CTableHeaderCell>
                                <CTableHeaderCell scope="col">Division</CTableHeaderCell>
                                <CTableHeaderCell scope="col">Conference</CTableHeaderCell>
                                <CTableHeaderCell scope="col">Power Ranking</CTableHeaderCell>
                                <CTableHeaderCell scope="col">State</CTableHeaderCell>
                            </CTableRow>
                        </CTableHead>
                        <CTableBody>
                            {missingTeamNames.map((team, index) => (
                                <CTableRow key={index}>
                                    <CTableDataCell>
                                        {team}
                                    </CTableDataCell>
                                    <CTableDataCell>
                                        <Select options={division} placeholder="Select Division"
                                        isSearchable
                                        // value={formData[index]?.division}
                                        onChange={(option) => handleInputChange(index, 'division', option.label)} />
                                    </CTableDataCell>
                                    <CTableDataCell>
                                        {/* value={formData[index]?.conference} */}
                                        <Select options={conference} placeholder="Select Conference"
                                        isSearchable isDisabled={isConference}
                                        onChange={(option) => handleInputChange(index, 'conference', option.label)} />
                                    </CTableDataCell>
                                    <CTableDataCell>
                                        <CFormInput
                                            type="number"
                                            // value={formData[index]?.powerRankings}
                                            onChange={(e) => handleInputChange(index, 'power_ranking', e.target.value)}
                                        />
                                    </CTableDataCell>
                                    <CTableDataCell>
                                        {/* value={formData[index]?.state} */}
                                        <Select options={states} placeholder="Select State"
                                        isSearchable
                                        onChange={(option) => handleInputChange(index, 'state', option.label)}/>
                                    </CTableDataCell>
                                </CTableRow>
                            ))}
                        </CTableBody>
                    </CTable>
                </CModalBody>
                <CModalFooter>
                    <button className="btn btn-secondary" onClick={onClose}>
                        Cancel
                    </button>
                    <button className="btn btn-primary" onClick={handleSubmit}>
                        Submit
                    </button>
                </CModalFooter>
            </CModal>

            <CModal visible={showMessageModal} onClose={() => setShowMessageModal(false)}>
            <CModalHeader>
                <CModalTitle>Notification</CModalTitle>
            </CModalHeader>
            <CModalBody>
                {modalMessage}
            </CModalBody>
            <CModalFooter>
                <button className="btn btn-primary" onClick={() => setShowMessageModal(false)}>
                    OK
                </button>
            </CModalFooter>
            </CModal>
        </>
    )
}

export default AddMissingTeams