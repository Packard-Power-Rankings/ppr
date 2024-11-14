// src/components/admin/CsvUpload.js
import React, { useState } from 'react';
import UpdateTeam from './UpdateTeam';
import CSVTable from './CsvTable'; // Import the existing CSVTable
import { parseCsvFile } from './CsvParser'; // Import the CSV parsing utility

const CsvUpload = ({ SportType, Gender, Level, isUploadDisabled }) => {
    const [file, setFile] = useState(null);
    const [errorMessage, setErrorMessage] = useState('');
    const [parsedData, setParsedData] = useState([]); // For holding parsed CSV data
    const [headers, setHeaders] = useState([]); // For holding CSV headers
    const [missingTeams, setMissingTeams] = useState([]);
    const [showUpdateForm, setShowUpdateForm] = useState(false);

    const getToken = () => {
        return localStorage.getItem('access_token');
    };

    const handleFileChange = (e) => {
        setFile(e.target.files[0]);
    };

    const handleParseFile = async () => {
        try {
            const data = await parseCsvFile(file);
            if (data.length > 0) {
                setHeaders(Object.keys(data[0])); // Capture headers from the first row
                setParsedData(data); // Set parsed CSV data for table display
            } else {
                setErrorMessage("CSV file is empty or has invalid content.");
            }
        } catch (error) {
            setErrorMessage(`Parsing error: ${error}`);
        }
    };

    const handleUploadSubmit = (e) => {
        e.preventDefault();
        handleParseFile();
    };

    const handleServerUploadSubmit = async () => {
        const token = getToken();
        if (!token) {
            setErrorMessage('Unauthorized: No token found');
            return;
        }

        const formData = new FormData();
        formData.append('sport_type', SportType);
        formData.append('gender', Gender);
        formData.append('level', Level);
        formData.append('csv_file', file);

        try {
            const response = await fetch('http://localhost:8000/admin/upload_csv/', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
                body: formData,
            });

            const data = await response.json();

            if (response.ok && data?.missing_teams) {
                setMissingTeams(data.missing_teams);
                setShowUpdateForm(true);
            } else {
                const errorText = typeof data.detail === 'object'
                    ? JSON.stringify(data.detail)
                    : data.detail || 'Upload failed. Please try again.';
                setErrorMessage(errorText);
            }
        } catch (error) {
            setErrorMessage('There was an issue with the upload. Please try again.');
        }
    };

    const handleUpdateSubmit = async (updatedTeams) => {
        const token = getToken();
        if (!token) {
            setErrorMessage('Unauthorized: No token found');
            return;
        }

        const formData = new URLSearchParams();
        formData.append('new_team', JSON.stringify({ teams: updatedTeams }));
        formData.append('sport_type', SportType);
        formData.append('gender', Gender);
        formData.append('level', Level);

        try {
            const response = await fetch('http://localhost:8000/admin/add_teams/', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Accept': 'application/json',
                },
                body: formData,
            });

            const data = await response.json();

            if (response.ok) {
                setMissingTeams([]);
                setShowUpdateForm(false);
                alert('Teams updated successfully!');
            } else {
                setErrorMessage(data.detail || 'Update failed. Please try again.');
            }
        } catch (error) {
            setErrorMessage('There was an issue with updating teams. Please try again.');
        }
    };

    return (
        <div>
            {/* CSV Upload Section */}
            <form onSubmit={handleUploadSubmit}>
                <input
                    type="file"
                    onChange={handleFileChange}
                    accept=".csv"
                    required
                    disabled={isUploadDisabled}
                />
                <button type="submit" disabled={isUploadDisabled}>Upload</button>
                {errorMessage && (
                    <p style={{ color: 'red' }}>{errorMessage}</p>
                )}
            </form>

            {/* Editable CSV Table */}
            {parsedData.length > 0 && (
                <div style={{ marginTop: '20px' }}> {/* Adjust margin size as needed */}
                    <CSVTable headers={headers} data={parsedData} setData={setParsedData} />
                    <button onClick={handleServerUploadSubmit}>Submit to Server</button>
                </div>
            )}

            {/* Update Teams Section (conditionally shown) */}
            {showUpdateForm && (
                <div style={{ marginBottom: '20px' }}>
                    <UpdateTeam
                        initialTeams={missingTeams.map((team) => ({
                            team_name: team,
                            power_ranking: '',
                            division: '',
                            conference: '',
                            state: '',
                        }))}
                        onUpdateSubmit={handleUpdateSubmit}
                    />
                </div>
            )}
        </div>
    );
};

export default CsvUpload;
