import React, { useEffect, useState } from "react";
import {
    CFormInput,
    CTable,
    CTableHead,
    CTableHeaderCell,
    CTableBody,
    CTableDataCell,
    CTableRow,
    CButton,
    CFooter,
    CModal,
    CModalHeader,
    CModalTitle,
    CModalBody,
    CModalFooter
} from "@coreui/react";
import api from "src/api";
import Papa from "papaparse";
import { useSelector } from "react-redux";
import AddMissingTeams from "./AddMissingTeams";


const AddTeams = () => {
    const sport = useSelector((state) => state.sport);
    const gender = useSelector((state) => state.gender);
    const level = useSelector((state) => state.level);
    const [ gameFile, setGameFile ] = useState([]);
    const [ teamNames, setTeamNames ] = useState([]);
    const [ missingTeams, setMissingTeams ] = useState([]);
    const [ showModal, setShowModal ] = useState(false);
    const [ fileMessage, setFileMessage ] = useState('');
    const [ filePopUp, setFilePopUp ] = useState(false);
    const [ fileName, setFileName ] = useState('');

    const handleFileUpload = (e) => {  // Reads the file and parses the csv file
        const file = e.target.files[0]
        if (!file) return;

        setFileName(file.name);
        const reader = new FileReader();
        reader.onload = (event) => {
            const csvData = event.target.result;
            Papa.parse(csvData, {
                complete: (result) => {
                    setGameFile(result.data);
                    extractTeams(result.data);
                },
                skipEmptyLines: true,
            })
        };
        reader.readAsText(file);
    };

    const handleSubmit = async () => {
        const csvString = Papa.unparse(gameFile);
        const blob = new Blob([csvString], { type: "text/csv" });
        const updateFile = new File([blob], `${fileName}`, { type: "text/csv" });

        const formData = new FormData();
        formData.append('csv_file', updateFile);
        try {
            const response = await api.post(
                `/upload_csv/?sport_type=${sport}&gender=${gender}&level=${level}`,
                formData,
                {
                    headers: {"Content-Type": 'multipart/form-data'},
                    withCredentials: true
                }
            );
            setFileMessage(response.data.message);
            setFilePopUp(true);
        } catch (error) {
            console.error("Failed to upload file", error);
        }
    }

    const extractTeams = (data) => {
        const teams = [];
        data.forEach((row) => {
            if (row[1]) teams.push(row[1]);
            if (row[2]) teams.push(row[2]);
        });
        setTeamNames([...teams]);
    }

    const checkMissingTeams = async () => {
        try {
            const response = await api.post(
                `/check-teams/?sport_type=${sport}&gender=${gender}&level=${level}`, teamNames,
                {
                    headers: {'Content-Type': "application/json"},
                    withCredentials: true
                }
            )
            if (response.data.missing_teams?.length > 0) {
                setMissingTeams(response.data.missing_teams);
                setShowModal(true);
            } else {
                console.warn("No teams need to be added");
            }
        } catch (error) {
            console.error("Error Occured Fetching Teams", error)
        }
    }

    useEffect(() => {
        if (teamNames.length > 0) {
            checkMissingTeams();
        }
    }, [teamNames])

    return (
        <div className="mb-3">
            <CFormInput
                type="file"
                accept=".csv"
                size="sm"
                id="formFile"
                onChange={handleFileUpload}
            />
            {gameFile.length > 0 && (
                <CTable>
                    <CTableHead>
                        <CTableRow>
                            <CTableHeaderCell scope="col">Date</CTableHeaderCell>
                            <CTableHeaderCell scope="col">Home Team</CTableHeaderCell>
                            <CTableHeaderCell scope="col">Away Team</CTableHeaderCell>
                            <CTableHeaderCell scope="col">Home Score</CTableHeaderCell>
                            <CTableHeaderCell scope="col">Away Score</CTableHeaderCell>
                            <CTableHeaderCell scope="col">Home Field Flag</CTableHeaderCell>
                        </CTableRow>
                    </CTableHead>
                    <CTableBody>
                        {gameFile.map((row, rowIndex) => (
                            <CTableRow key={rowIndex}>
                                {row.map((cell, colIndex) => (
                                    <CTableDataCell key={colIndex}>
                                        <CFormInput
                                            type="text"
                                            value={cell}
                                            onChange={(e) => {
                                                const updateFile = [...gameFile];
                                                updateFile[rowIndex][colIndex] = e.target.value;
                                                setGameFile(updateFile);
                                            }}
                                        />
                                    </CTableDataCell>
                                ))}
                            </CTableRow>
                        ))}
                    </CTableBody>
                </CTable>
            )}
            <CModal visible={filePopUp} onClose={() => setFilePopUp(false)}>
                <CModalHeader>
                    <CModalTitle>Notification</CModalTitle>
                </CModalHeader>
                <CModalBody>
                    {fileMessage}
                </CModalBody>
                <CModalFooter>
                    <button className="btn btn-primary" onClick={() => setFilePopUp(false)}>
                        OK
                    </button>
                </CModalFooter>
            </CModal>
            <CFooter position="sticky" className="py-4">
                <CButton onClick={handleSubmit} as="input" type="submit" color="primary" value="Submit" />
            </CFooter>
            {showModal && (
                <AddMissingTeams
                    missingTeamNames={missingTeams}
                    onClose={() => setShowModal(false)}
                />
            )}
        </div>
    )
}

export default AddTeams