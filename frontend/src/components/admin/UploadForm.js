import React, { useState } from 'react';
import UpdateTeam from './UpdateTeam';
import RunAlgorithm from './RunAlgorithm';
import CsvUpload from './CsvUpload';

const UploadForm = ({ initialSportType, initialGender, initialLevel }) => {
    const [missingTeams, setMissingTeams] = useState([]);
    const [showUpdateForm, setShowUpdateForm] = useState(false);
    const [isUploadDisabled, setIsUploadDisabled] = useState(false);
    const [showRunAlgorithm, setShowRunAlgorithm] = useState(true); // Always show Run Algorithm
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

        console.log('FormData being sent:');
        formData.forEach((value, key) => {
            console.log(key, value);
        });

        try {
            const response = await fetch('http://localhost:8000/admin/add_teams/', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json();
                console.error('Error details:', errorData);
                setErrorMessage(errorData.detail || 'Submission failed.');
                throw new Error(`Fetch error: ${response.statusText}`);
            }

            setErrorMessage('');
        } catch (error) {
            console.error('Fetch error:', error);
            setErrorMessage('There was an issue with your request.');
        }
    };

    const handleRunAlgorithm = async (runCount) => {
        await fetch('http://localhost:8000/run_algorithm/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ run_count: runCount }),
        });
    };

    return (
        <div>
            <h2>Upload New Sports Data</h2>
            <CsvUpload
                initialSportType={initialSportType}
                initialGender={initialGender}
                initialLevel={initialLevel}
                onUploadComplete={handleUploadComplete}
                isUploadDisabled={isUploadDisabled}
            />

            {errorMessage && <p style={{ color: 'red' }}>{errorMessage}</p>}

            {showUpdateForm && (
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
            )}

            {/* Always show RunAlgorithm component */}
            <RunAlgorithm onRun={handleRunAlgorithm} />
        </div>
    );
};

export default UploadForm;
