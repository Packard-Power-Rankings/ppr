// src/components/admin/AdminPage.js
import React, { useState } from 'react';
import SportForm from './SportForm';
import CsvUpload from './CsvUpload';
import DeleteForm from './DeleteForm';
import RunAlgorithm from './RunAlgorithm';

const AdminPage = () => {
    const [showUploadForm, setShowUploadForm] = useState(false);
    const [sportData, setSportData] = useState({ sportType: '', gender: '', level: '' });
    const [showSportSelection, setShowSportSelection] = useState(true); // Show sport selection by default

    // Handle SportForm submission
    const handleSportFormSubmit = (data) => {
        setSportData(data);
        setShowSportSelection(false); // Hide sport selection after selection
    };

    return (
        <div>
            <h1>Packard Power Rankings Admin Page</h1>

            {/* Sport Selection Form Section */}
            {showSportSelection ? (
                <div>
                    <h2>Select Sport Data</h2>
                    <SportForm onSubmit={handleSportFormSubmit} />
                </div>
            ) : (
                <div>
                    <h3>Selected: {sportData.sportType} - {sportData.gender} - {sportData.level}</h3>

                    {/* Button to change sport selection below the selected info */}
                    <button onClick={() => setShowSportSelection(true)}>Change Sport Selection</button>

                    {/* Show other Admin Operations after selection */}
                    <div style={{ marginTop: '20px' }}>
                        <h2>Upload New Sports Data</h2>
                        <CsvUpload
                            SportType={sportData.sportType}
                            Gender={sportData.gender}
                            Level={sportData.level}
                            isUploadDisabled={false} // Enable or disable upload as needed
                        />
                    </div>

                    <div style={{ marginTop: '20px' }}>
                        <h2>Run Algorithm</h2>
                        <RunAlgorithm
                            sportType={sportData.sportType}
                            gender={sportData.gender}
                            level={sportData.level}
                        />
                    </div>

                    <div style={{ marginTop: '20px' }}>
                        <h2>Delete Sports Data</h2>
                        <DeleteForm />
                    </div>
                </div>
            )}
        </div>
    );
};

export default AdminPage;
