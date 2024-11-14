import React, { useState } from 'react';
import UpdateTeam from './UpdateTeam';

const CsvUpload = ({ initialSportType, initialGender, initialLevel, isUploadDisabled }) => {
    const [file, setFile] = useState(null);
    const [errorMessage, setErrorMessage] = useState('');
    const [missingTeams, setMissingTeams] = useState([]);
    const [showUpdateForm, setShowUpdateForm] = useState(false);

    const getToken = () => {
        return localStorage.getItem('access_token');
    };

    const handleUploadSubmit = async (e) => {
        e.preventDefault();

        const token = getToken();
        if (!token) {
            setErrorMessage('Unauthorized: No token found');
            return;
        }

        const formData = new FormData();
        formData.append('sport_type', initialSportType);
        formData.append('gender', initialGender);
        formData.append('level', initialLevel);
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

            if (response.ok && data && data.missing_teams) {
                setMissingTeams(data.missing_teams);
                setShowUpdateForm(true);
            } else {
                setErrorMessage(data.detail || 'Upload failed. Please try again.');
            }
        } catch (error) {
            setErrorMessage('There was an issue with the upload. Please try again.');
        }
    };

    const handleUpdateSubmit = async (teams) => {
        const token = getToken();
        if (!token) {
            setErrorMessage('Unauthorized: No token found');
            return;
        }

        const formData = new FormData();
        formData.append('teams', JSON.stringify(teams));

        try {
            const response = await fetch('http://localhost:8000/admin/add_teams/', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json();
                setErrorMessage(errorData.detail || 'Submission failed.');
                throw new Error(`Fetch error: ${response.statusText}`);
            }

            setErrorMessage('');
        } catch (error) {
            setErrorMessage('There was an issue with your request.');
        }
    };

    return (
        <div>
            {/* CSV Upload Section */}
            <form onSubmit={handleUploadSubmit}>
                <input
                    type="file"
                    onChange={(e) => setFile(e.target.files[0])}
                    accept=".csv"
                    required
                    disabled={isUploadDisabled}
                />
                <button type="submit" disabled={isUploadDisabled}>Upload</button>
                {errorMessage && <p style={{ color: 'red' }}>{errorMessage}</p>}
            </form>

            {/* Update Teams Section (conditionally shown) */}
            {showUpdateForm && (
                <div style={{ marginTop: '20px' }}>
                    <UpdateTeam
                        initialTeams={missingTeams.map((team) => ({
                            team_name: team,
                            score: '',
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
