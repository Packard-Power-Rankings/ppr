// src/components/admin/AdminPage.js
import React, { useState } from 'react';
import SportForm from './SportForm';
import UploadForm from './UploadForm';
import DeleteForm from './DeleteForm';
import RunAlgorithm from './RunAlgorithm';

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
        if (newTeamsDetected) {
            setShowUpdateForm(true);
        }
    };

    return (
        <div>
            <h1>Packard Power Rankings Admin Page</h1>

            {/* Sport Form Section */}
            <div style={{ borderTop: '1px solid #ccc', paddingTop: '20px', marginBottom: '20px' }}>
                <h2>Upload New Sports Data</h2>
                {!showUploadForm ? (
                    <SportForm onSubmit={handleSportFormSubmit} />
                ) : (
                    <>
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

            {/* Optional: Update Form Section if Needed */}
            {showUpdateForm && (
                <div style={{ borderTop: '1px solid #ccc', paddingTop: '20px', marginBottom: '20px' }}>
                    <h2>Update Team Data</h2>
                    {/* Additional form or information related to team updates */}
                </div>
            )}

            {/* Run Algorithm Section */}
            <div style={{ borderTop: '1px solid #ccc', paddingTop: '20px', marginBottom: '20px' }}>
                <h2>Run Algorithm</h2>
                <RunAlgorithm />
            </div>

            {/* Delete Form Section */}
            <div style={{ borderTop: '1px solid #ccc', paddingTop: '20px', marginBottom: '20px' }}>
                <h2>Delete Sports Data</h2>
                <DeleteForm />
            </div>
        </div>
    );
};

export default AdminPage;
