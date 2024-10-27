import React, { useState } from 'react';
import SportForm from './SportForm';
import UploadForm from './UploadForm';
import UpdateTeam from './UpdateTeam';

const AdminPage = () => {
    const [showUploadForm, setShowUploadForm] = useState(false);
    const [showUpdateForm, setShowUpdateForm] = useState(false);
    const [sportData, setSportData] = useState({ sportType: '', gender: '', level: '' });
    const [runCount, setRunCount] = useState(1);

    // Handle SportForm submission
    const handleSportFormSubmit = (data) => {
        setSportData(data);
        setShowUploadForm(true);
    };

    // Handle conditional team update based on CSV upload results
    const handleCsvUploadComplete = (newTeamsDetected) => {
        console.log('CSV upload complete. New teams detected:', newTeamsDetected);
        // Show update form only if there are new teams or data mismatches
        if (newTeamsDetected) {
            setShowUpdateForm(true);
        }
    };

    const handleUpdateTeamsSubmit = (teamName) => {
        console.log('Updating team:', teamName);
        // Make an API call here to update the team based on the `sportData` and `teamName`
        setShowUpdateForm(false);
    };

    const handleSubmit = () => {
        console.log(`Submitting data with ${runCount} run(s)`);
        // Trigger the backend API call to run the algorithm with `runCount`
    };

    return (
        <div>
            <h1>Packard Power Rankings Admin Page</h1>
            <h2>Upload New Sports Data</h2>

            {/* Step 1: Display the SportForm initially */}
            {!showUploadForm ? (
                <SportForm onSubmit={handleSportFormSubmit} />
            ) : (
                <>
                    {/* Step 2: CSV Upload */}
                    <h3>Upload CSV for {sportData.sportType} - {sportData.gender} - {sportData.level}</h3>
                    <UploadForm
                        initialSportType={sportData.sportType}
                        initialGender={sportData.gender}
                        initialLevel={sportData.level}
                        onComplete={handleCsvUploadComplete}  // Trigger this function when upload is complete
                    />

                    {/* Step 3: Optional Update */}
                    {showUpdateForm && (
                        <UpdateTeam
                            sportType={sportData.sportType}
                            gender={sportData.gender}
                            level={sportData.level}
                            onSubmit={handleUpdateTeamsSubmit}
                        />
                    )}

                    {/* Step 4: Submission with Run Count, only show after update */}
                    {showUpdateForm && (
                        <div>
                            <h3>Specify Number of Runs</h3>
                            <input
                                type="number"
                                min="1"
                                value={runCount}
                                onChange={(e) => setRunCount(e.target.value)}
                            />
                            <button onClick={handleSubmit}>Submit</button>
                        </div>
                    )}
                </>
            )}
        </div>
    );
};

export default AdminPage;
