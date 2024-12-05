// src/components/admin/AdminPage.js
import React, { useState } from 'react';
import SportForm from './SportForm';
import CsvUpload from './CsvUpload';
import DeleteForm from './DeleteForm';
import RunAlgorithm from './RunAlgorithm';

const AdminPage = () => {
    const [showUploadForm, setShowUploadForm] = useState(false);
    const [sportData, setSportData] = useState({ sportType: '', gender: '', level: '' });

    // Handle SportForm submission
    const handleSportFormSubmit = (data) => {
        setSportData(data);
        setShowUploadForm(true);
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
                    <div>
                        <h3>Upload CSV for {sportData.sportType} - {sportData.gender} - {sportData.level}</h3>
                        <CsvUpload
                            SportType={sportData.sportType}
                            Gender={sportData.gender}
                            Level={sportData.level}
                            isUploadDisabled={false} // Enable or disable upload as needed
                        />
                    </div>
                )}
            </div>

            {/* Run Algorithm Section */}
            <div style={{ borderTop: '1px solid #ccc', paddingTop: '20px', marginBottom: '20px' }}>
                <h2>Run Algorithm</h2>
                {/* Pass sportData as props to RunAlgorithm */}
                <RunAlgorithm
                    sportType={sportData.sportType}
                    gender={sportData.gender}
                    level={sportData.level}
                />
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
