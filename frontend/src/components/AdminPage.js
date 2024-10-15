import React, { useState } from 'react';
import SportForm from './SportForm';
import UploadForm from './UploadForm';  // Import the UploadForm component

const AdminPage = () => {
    const [showUploadForm, setShowUploadForm] = useState(false);
    const [sportData, setSportData] = useState({
        sportType: '',
        gender: '',
        level: ''
    });

    // Function to handle SportForm submission
    const handleSportFormSubmit = (data) => {
        console.log('SportForm submitted with:', data);
        setSportData(data); // Save the data to pass to the UploadForm
        setShowUploadForm(true); // Show the UploadForm after SportForm is submitted
    };

    return (
        <div>
            <h1>Packard Power Rankings Admin Page</h1>
            <h2>Upload New Sports Data</h2>

            {/* Conditionally render SportForm or UploadForm based on showUploadForm state */}
            {!showUploadForm ? (
                <SportForm onSubmit={handleSportFormSubmit} />
            ) : (
                <>
                    {/* Display a header for the CSV upload section */}
                    <h3>Upload CSV for {sportData.sportType} - {sportData.gender} - {sportData.level}</h3>
                    <UploadForm
                        initialSportType={sportData.sportType}
                        initialGender={sportData.gender}
                        initialLevel={sportData.level}
                    />
                </>
            )}
        </div>
    );
};

export default AdminPage;
