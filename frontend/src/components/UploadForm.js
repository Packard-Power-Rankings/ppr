import React, { useState } from 'react';

const UploadForm = ({ initialSportType, initialGender, initialLevel }) => {
    const [file, setFile] = useState(null);
    const [missingTeams, setMissingTeams] = useState([]);
    const [teamDetails, setTeamDetails] = useState([]);
    const [showUpdateForm, setShowUpdateForm] = useState(false);
    const [errorMessage, setErrorMessage] = useState('');
    const [isUploadDisabled, setIsUploadDisabled] = useState(false);
    const [runCount, setRunCount] = useState(1); // For number of times to run the algorithm
    const [showRunAlgorithm, setShowRunAlgorithm] = useState(false); // New state for running algorithm

    const handleUploadSubmit = (e) => {
        e.preventDefault();
        const formData = new FormData();
        formData.append('sport_type', initialSportType);
        formData.append('gender', initialGender);
        formData.append('level', initialLevel);
        formData.append('csv_file', file);

        fetch('http://localhost:8000/admin/upload_csv/', {
            method: 'POST',
            body: formData,
        })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(errData => {
                        setErrorMessage(errData.detail || 'Upload failed.');
                        throw new Error('Network response was not ok');
                    });
                }
                setErrorMessage('');
                setIsUploadDisabled(true);
                return response.json();
            })
            .then(data => {
                setMissingTeams(data.missing_teams);
                setTeamDetails(data.missing_teams.map(team => ({
                    team_name: team,
                    score: '',
                    power_ranking: '',
                    division: '',
                    conference: '',
                    state: '',
                })));
                setShowUpdateForm(true);
            })
            .catch(error => {
                console.error('There was a problem with your fetch operation:', error);
            });
    };

    const handleUpdateSubmit = (e) => {
        e.preventDefault();
        fetch('http://localhost:8000/admin/add_teams/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(teamDetails),
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(() => {
                // After successful update, show the run algorithm step
                setShowRunAlgorithm(true); // Update visibility state for run algorithm
            })
            .catch(error => console.error('There was a problem with your fetch operation:', error));
    };

    const handleRunAlgorithm = () => {
        if (runCount < 1 || runCount > 30) {
            setErrorMessage('Please enter a value between 1 and 30.');
            return;
        }

        fetch('http://localhost:8000/run_algorithm/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ run_count: runCount }), // Pass the run count
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                // Handle success response from /run_algorithm
                console.log('Algorithm run successful:', data);
                // Optionally reset or handle any state here
            })
            .catch(error => console.error('There was a problem with your fetch operation:', error));
    };

    const handleDetailChange = (index, field, value) => {
        const newDetails = [...teamDetails];
        newDetails[index][field] = value;
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
                                    type="number"
                                    placeholder="Power Ranking"
                                    value={team.power_ranking}
                                    onChange={(e) => handleDetailChange(index, 'power_ranking', e.target.value)}
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
