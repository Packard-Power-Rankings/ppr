import React from "react";
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

const AddMissingTeams = ({ missingTeamNames, onClose }) => {
    const handleSubmit = async (e) => {
        // Add teams to database through backend endpoint
    }

    return (
        <CModal size="xl" visible={true} onClose={onClose}>
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
                                <CTableDataCell>{team}</CTableDataCell>
                                <CTableDataCell>
                                    <Select />
                                </CTableDataCell>
                                <CTableDataCell>
                                    <Select />
                                </CTableDataCell>
                                <CTableDataCell>
                                    <CFormInput
                                        type="number"
                                    />
                                </CTableDataCell>
                                <CTableDataCell>
                                    <Select />
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
                <button className="btn btn-primary">
                    Submit
                </button>
            </CModalFooter>
        </CModal>
    )
}

export default AddMissingTeams