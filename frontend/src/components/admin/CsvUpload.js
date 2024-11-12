// src/components/admin/CsvUpload.js
import React, { useState } from 'react';

const CsvUpload = ({ initialSportType, initialGender, initialLevel, onUploadComplete, isUploadDisabled }) => {
    const [file, setFile] = useState(null);
    const [errorMessage, setErrorMessage] = useState('');

    const getToken = () => {
        // Retrieve the JWT token from localStorage
        return localStorage.getItem('access_token');
    };

    const handleUploadSubmit = async (e) => {
        e.preventDefault();

        const token = getToken(); // Retrieve the token
        if (!token) {
            setErrorMessage('Unauthorized: No token found');
            return;
        }

        const formData = new FormData();
        formData.append('sport_type', initialSportType);
        formData.append('gender', initialGender);
        formData.append('level', initialLevel);
        formData.append('csv_file', file);

        try {
            const response = await fetch('http://localhost:8000/admin/upload_csv/', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,  // Include the JWT token in the headers
                },
                body: formData,
            });
            const data = await response.json();

            if (response.ok && data && data.missing_teams) {
                onUploadComplete(data.missing_teams); // Call the callback with missing teams
            } else {
                setErrorMessage(data.detail || 'Upload failed. Please try again.');
            }
        } catch (error) {
            console.error('Upload error:', error);
            setErrorMessage('There was an issue with the upload. Please try again.');
        }
    };

    return (
        <form onSubmit={handleUploadSubmit}>
            <input
                type="file"
                onChange={(e) => setFile(e.target.files[0])}
                accept=".csv"
                required
                disabled={isUploadDisabled}
            />
            <button type="submit" disabled={isUploadDisabled}>Upload</button>
            {errorMessage && <p style={{ color: 'red' }}>{errorMessage}</p>}
        </form>
    );
};

export default CsvUpload;
