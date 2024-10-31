import React, { useState } from 'react';

const UploadForm = ({ initialSportType, initialGender, initialLevel }) => {
    const [file, setFile] = useState(null);
    const [missingTeams, setMissingTeams] = useState([]);
    const [teamDetails, setTeamDetails] = useState([]);
    const [showUpdateForm, setShowUpdateForm] = useState(false);
    const [errorMessage, setErrorMessage] = useState('');
    const [isUploadDisabled, setIsUploadDisabled] = useState(false);
    const [runCount, setRunCount] = useState(1);
    const [showRunAlgorithm, setShowRunAlgorithm] = useState(false);

    const fetchWithErrorHandling = async (url, options) => {
        try {
            const response = await fetch(url, options);
            if (!response.ok) {
                const errorData = await response.json();
                setErrorMessage(errorData.detail || 'Upload failed.');
                console.error('Error details:', errorData);
                throw new Error(`Fetch error: ${response.statusText}`);
            }
            return response.json();
        } catch (error) {
            console.error('Fetch error:', error);
            setErrorMessage('There was an issue with your request.');
        }
    };

    const handleUploadSubmit = async (e) => {
        e.preventDefault();
        const formData = new FormData();
        formData.append('sport_type', initialSportType);
        formData.append('gender', initialGender);
        formData.append('level', initialLevel);
        formData.append('csv_file', file);

        const data = await fetchWithErrorHandling('http://localhost:8000/admin/upload_csv/', {
            method: 'POST',
            body: formData,
        });

        if (data && data.missing_teams) {
            setMissingTeams(data.missing_teams);
            setTeamDetails(data.missing_teams.map((team) => ({
                team_name: team,
                score: '',
                power_ranking: '',
                division: '',
                conference: '',
                state: '',
            })));
            setShowUpdateForm(true);
        }
    };

    const handleUpdateSubmit = async (e) => {
        e.preventDefault();
        const teamsData = teamDetails.map((team) => ({
            team_name: team.team_name,
            power_ranking: parseFloat(team.power_ranking) || 0,
            division: team.division || null,
            conference: team.conference || null,
            state: team.state || null,
        }));
    
        const payload = {
            teams: teamsData,
            sport_type: initialSportType,
            gender: initialGender,
            level: initialLevel,
        };
    
        try {
            const response = await fetch('http://localhost:8000/admin/add_teams/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'accept': 'application/json',
                },
                body: JSON.stringify(payload),
            });
    
            if (!response.ok) {
                const errorData = await response.json();
                console.error('Error details:', errorData);
                setErrorMessage(errorData.detail || 'Submission failed.');
                throw new Error(`Fetch error: ${response.statusText}`);
            }
    
            setErrorMessage('');
            setShowRunAlgorithm(true);
        } catch (error) {
            console.error('Fetch error:', error);
            setErrorMessage('There was an issue with your request.');
        }
    };

    const handleRunAlgorithm = async () => {
        if (runCount < 1 || runCount > 30) {
            setErrorMessage('Please enter a value between 1 and 30.');
            return;
        }

        await fetchWithErrorHandling('http://localhost:8000/run_algorithm/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ run_count: runCount }),
        });
    };

    const handleDetailChange = (index, field, value) => {
        const newDetails = [...teamDetails];
        newDetails[index][field] = field === 'power_ranking' ? parseFloat(value) : value;
        setTeamDetails(newDetails);
    };

    return (
        <div>
            <h2>Upload New Sports Data</h2>
            <form onSubmit={handleUploadSubmit}>
                <input
                    type="file"
                    onChange={(e) => setFile(e.target.files[0])}
                    accept=".csv"
                    required
                    disabled={isUploadDisabled}
                />
                <button type="submit" disabled={isUploadDisabled}>Upload</button>
            </form>

            {errorMessage && <p style={{ color: 'red' }}>{errorMessage}</p>}

            {showUpdateForm && (
                <div>
                    <h2>Update Team Information</h2>
                    <form onSubmit={handleUpdateSubmit}>
                        {teamDetails.map((team, index) => (
                            <div key={index}>
                                <input
                                    type="text"
                                    placeholder="Team Name"
                                    value={team.team_name}
                                    onChange={(e) => handleDetailChange(index, 'team_name', e.target.value)}
                                    required
                                />
                                <input
                                    type="text"
                                    placeholder="Division"
                                    value={team.division}
                                    onChange={(e) => handleDetailChange(index, 'division', e.target.value)}
                                />
                                <input
                                    type="text"
                                    placeholder="Conference"
                                    value={team.conference}
                                    onChange={(e) => handleDetailChange(index, 'conference', e.target.value)}
                                />
                                <input
                                    type="number"
                                    placeholder="Power Ranking"
                                    value={team.power_ranking}
                                    onChange={(e) => handleDetailChange(index, 'power_ranking', e.target.value)}
                                />
                                <input
                                    type="text"
                                    placeholder="State"
                                    value={team.state}
                                    onChange={(e) => handleDetailChange(index, 'state', e.target.value)}
                                />
                            </div>
                        ))}
                        <button type="submit">Update Teams</button>
                    </form>
                </div>
            )}

            {showRunAlgorithm && (
                <div>
                    <h2>Run Algorithm</h2>
                    <input
                        type="number"
                        placeholder="Number of Times to Run (1-30)"
                        value={runCount}
                        onChange={(e) => setRunCount(Math.max(1, Math.min(30, e.target.value)))}
                        min="1"
                        max="30"
                    />
                    <button onClick={handleRunAlgorithm}>Run Algorithm</button>
                </div>
            )}
        </div>
    );
};

export default UploadForm;
