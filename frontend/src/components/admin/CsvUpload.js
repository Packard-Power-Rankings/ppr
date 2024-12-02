// src/components/admin/CsvUpload.js
import React, { useState } from 'react';
import UpdateTeam from './UpdateTeam';
import CSVTable from './CsvTable';
import { parseCsvFile } from './CsvParser';
import { useNavigate } from 'react-router-dom'; // Assuming React Router for navigation

const CsvUpload = ({ SportType, Gender, Level, isUploadDisabled }) => {
    const [file, setFile] = useState(null);
    const [errorMessage, setErrorMessage] = useState('');
    const [parsedData, setParsedData] = useState([]); // For holding parsed CSV data
    const [headers, setHeaders] = useState([]); // For holding CSV headers
    const [missingTeams, setMissingTeams] = useState([]);
    const [showUpdateForm, setShowUpdateForm] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false); // Track submission state
    const navigate = useNavigate(); // To handle redirection
    const [successMessage, setSuccessMessage] = useState('');

    const getToken = () => {
        return localStorage.getItem('access_token');
    };

    const handleAuthError = (response) => {
        if (response.status === 401) {
            localStorage.removeItem('access_token'); // Clear expired token
            navigate('/login'); // Redirect to login page
        } else {
            response.text().then((text) => {
                setErrorMessage(text || 'An error occurred. Please try again.');
            });
        }
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
        setIsSubmitting(true); // Disable the submit button
        handleParseFile();
    };

    const handleServerUploadSubmit = async () => {
        const token = getToken();
        if (!token) {
            setErrorMessage('Unauthorized: No token found');
            navigate('/login');
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

            if (response.ok) {
                const data = await response.json();
                if (data.missing_teams) {
                    setMissingTeams(data.missing_teams);
                    setShowUpdateForm(true);
                } else {
                    setErrorMessage('Upload completed successfully, but no missing teams were found.');
                }
                setSuccessMessage('CSV uploaded successfully!');
            } else {
                handleAuthError(response);
            }
        } catch (error) {
            setErrorMessage('There was an issue with the upload. Please try again.');
        } finally {
            setIsSubmitting(false); // Re-enable the submit button
        }
    };

    const handleUpdateSubmit = async (updatedTeams) => {
        const token = getToken();
        if (!token) {
            setErrorMessage('Unauthorized: No token found');
            navigate('/login');
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
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: formData,
            });

            if (response.ok) {
                setMissingTeams([]);
                setShowUpdateForm(false);
                alert('Teams updated successfully!');
            } else {
                handleAuthError(response);
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
                    disabled={isUploadDisabled || isSubmitting} // Disable if uploading
                />
                <button type="submit" disabled={isUploadDisabled || isSubmitting}>Upload</button>
                {errorMessage && (
                    <p style={{ color: 'red' }}>{errorMessage}</p>
                )}
            </form>

            {/* Editable CSV Table */}
            {parsedData.length > 0 && (
                <div style={{ marginTop: '20px' }}>
                    <CSVTable headers={headers} data={parsedData} setData={setParsedData} />
                    <button onClick={handleServerUploadSubmit}>Submit to Server</button>
                    {successMessage && (
                        <p style={{ color: 'green' }}>{successMessage}</p>
                    )}
                </div>
            )}

            {/* Show Update Team Information only if there are missing teams */}
            {missingTeams.length > 0 && showUpdateForm && (
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
