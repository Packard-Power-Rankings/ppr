import React, { useState } from 'react';
import UpdateTeam from './UpdateTeam';
import RunAlgorithm from './RunAlgorithm';
import CsvUpload from './CsvUpload';

const UploadForm = ({ initialSportType, initialGender, initialLevel }) => {
    const [missingTeams, setMissingTeams] = useState([]);
    const [showUpdateForm, setShowUpdateForm] = useState(false);
    const [isUploadDisabled, setIsUploadDisabled] = useState(false);
    const [errorMessage, setErrorMessage] = useState('');

    const handleUploadComplete = (teams) => {
        setMissingTeams(teams);
        setShowUpdateForm(true);
        setIsUploadDisabled(true); // Disable upload buttons after successful upload
    };

    const handleUpdateSubmit = async (teamsData) => {
        const formData = new FormData();

        // Append teams data
        const teamsArray = teamsData.map((team) => ({
            team_name: team.team_name,
            power_ranking: parseFloat(team.power_ranking),
            division: team.division || null,
            conference: team.conference || null,
            state: team.state || null,
        }));

        formData.append('teams', JSON.stringify(teamsArray));

        // Append additional fields
        formData.append('sport_type', initialSportType);
        formData.append('gender', initialGender);
        formData.append('level', initialLevel);

        try {
            const response = await fetch('http://localhost:8000/admin/add_teams/', {
                method: 'POST',
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

    const handleRunAlgorithm = async (runCount) => {
        const formData = new FormData();
        formData.append('iterations', runCount);                // Add runCount as iterations
        formData.append('sport_type', initialSportType);        // Add sport_type
        formData.append('gender', initialGender);               // Add gender
        formData.append('level', initialLevel);                 // Add level

        try {
            const response = await fetch('http://localhost:8000/admin/run_algorithm/', {
                method: 'POST',
                body: formData,  // Pass FormData in the body
            });

            const data = await response.json();
            console.log(data);  // Log the full response to see what's inside `detail`

            if (data && data.detail) {
                // Check if detail is an array, and extract the error message from the object
                const errorDetail = data.detail[0];
                if (errorDetail && errorDetail.msg) {
                    setErrorMessage(errorDetail.msg);  // Display the msg from the error
                } else {
                    setErrorMessage('An unknown error occurred.');
                }
            }

            // Handle response data as needed
            console.log('Algorithm run successful:', data);

        } catch (error) {
            setErrorMessage('There was an issue with your request.');
            console.error('Fetch Error:', error);
        }
    };

    return (
        <div>
            <h2>Upload New Sports Data</h2>
            {/* CSV Upload Section */}
            <div style={{ marginBottom: '20px' }}>
                <CsvUpload
                    initialSportType={initialSportType}
                    initialGender={initialGender}
                    initialLevel={initialLevel}
                    onUploadComplete={handleUploadComplete}
                    isUploadDisabled={isUploadDisabled}
                />
            </div>

            {/* Display error message if any */}
            {errorMessage && <p style={{ color: 'red' }}>{errorMessage}</p>}

            {/* Update Teams Section (conditionally shown) */}
            {showUpdateForm && (
                <div style={{ marginBottom: '20px' }}>
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

            {/* Run Algorithm Section (always shown as separate) */}
            <div style={{ borderTop: '1px solid #ccc', paddingTop: '20px' }}>
                <RunAlgorithm onRun={handleRunAlgorithm} />
            </div>
        </div>
    );
};

export default UploadForm;
