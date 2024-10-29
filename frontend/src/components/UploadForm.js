import React, { useState } from 'react';

const UploadForm = ({ initialSportType, initialGender, initialLevel }) => {
    const [file, setFile] = useState(null);
    const [updateTeamName, setUpdateTeamName] = useState('');  // For updating team
    const [updateScore, setUpdateScore] = useState('');        // For updating team
    const [showUpdateForm, setShowUpdateForm] = useState(false); // Control visibility of update form
    const [errorMessage, setErrorMessage] = useState(''); // State for error messages

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
                    // Handle different response statuses here
                    return response.json().then(errData => {
                        // Set the error message from the response detail
                        setErrorMessage(errData.detail || 'Upload failed.');
                        throw new Error('Network response was not ok');
                    });
                }
                // Show the update form after successful upload
                setShowUpdateForm(true);
                setErrorMessage(''); // Clear any previous error messages
                return response.json();
            })
            .then(data => console.log(data))
            .catch(error => {
                console.error('There was a problem with your fetch operation:', error);
            });
    };

    const handleUpdateSubmit = (e) => {
        e.preventDefault();
        // Send a request to update the team info
        fetch('http://localhost:8000/admin/add_teams', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                team_name: updateTeamName,
                score: updateScore,
            }),
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => console.log(data))
            .catch(error => console.error('There was a problem with your fetch operation:', error));
    };

    return (
        <div>
            {/* Section for Uploading New Sports Data */}
            <h2>Upload New Sports Data</h2>
            <form onSubmit={handleUploadSubmit}>
                <input
                    type="file"
                    onChange={(e) => setFile(e.target.files[0])}
                    accept=".csv"
                    required
                />
                <button type="submit">Upload</button>
            </form>

            {/* Display Error Message if exists */}
            {errorMessage && <p style={{ color: 'red' }}>{errorMessage}</p>}

            {/* Conditionally Render the Update Team Information Section */}
            {showUpdateForm && (
                <div>
                    <h2>Update Team Information</h2>
                    <form onSubmit={handleUpdateSubmit}>
                        <input
                            type="text"
                            placeholder="Team Name"
                            value={updateTeamName}
                            onChange={(e) => setUpdateTeamName(e.target.value)}
                            required
                        />
                        <input
                            type="number"
                            placeholder="Score"
                            value={updateScore}
                            onChange={(e) => setUpdateScore(e.target.value)}
                            required
                        />
                        <button type="submit">Update Team</button>
                    </form>
                </div>
            )}
        </div>
    );
};

export default UploadForm;
