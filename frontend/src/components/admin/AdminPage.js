import React, { useState } from 'react';
import SportForm from './SportForm';
import UploadForm from './UploadForm';

const AdminPage = () => {
    const [showUploadForm, setShowUploadForm] = useState(false);
    const [showUpdateForm, setShowUpdateForm] = useState(false);
    const [sportData, setSportData] = useState({ sportType: '', gender: '', level: '' });

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

    return (
        <div>
            <h1>Packard Power Rankings Admin Page</h1>
            <h2>Upload New Sports Data</h2>

            {/* Step 1: Display the SportForm initially */}
            {!showUploadForm ? (
                <SportForm onSubmit={handleSportFormSubmit} />
            ) : (
                <>
                    {/* Step 2: CSV Upload Handling */}
                    <h3>Upload CSV for {sportData.sportType} - {sportData.gender} - {sportData.level}</h3>
                    <UploadForm
                        initialSportType={sportData.sportType}
                        initialGender={sportData.gender}
                        initialLevel={sportData.level}
                        onComplete={handleCsvUploadComplete}
                    />
                </>
            )}
        </div>
    );
};

export default AdminPage;
