// src/components/UploadForm.js
import React, { useState } from 'react';

const UploadForm = () => {
    const [file, setFile] = useState(null);
    const [sportType, setSportType] = useState('');
    const [gender, setGender] = useState('');
    const [level, setLevel] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        const formData = new FormData();
        formData.append('csv_file', file);
        formData.append('input', JSON.stringify({ sport_type: sportType, gender, level }));

        try {
            const response = await fetch('http://localhost:8000/admin/', {
                method: 'POST',
                body: formData,
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                },
            });

            const data = await response.json();
            console.log('Response from server:', data);
        } catch (error) {
            console.error('Error uploading file:', error);
        }
    };

    return (
        <form onSubmit={handleSubmit}>
            <input
                type="file"
                onChange={(e) => setFile(e.target.files[0])}
                accept=".csv"
                required
            />
            <input
                type="text"
                placeholder="Sport Type"
                value={sportType}
                onChange={(e) => setSportType(e.target.value)}
                required
            />
            <input
                type="text"
                placeholder="Gender"
                value={gender}
                onChange={(e) => setGender(e.target.value)}
                required
            />
            <input
                type="text"
                placeholder="Level"
                value={level}
                onChange={(e) => setLevel(e.target.value)}
                required
            />
            <button type="submit">Upload</button>
        </form>
    );
};

export default UploadForm;
