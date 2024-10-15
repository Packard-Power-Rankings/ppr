import React, { useState } from 'react';

const UploadForm = ({ initialSportType, initialGender, initialLevel }) => {
    const [file, setFile] = useState(null);

    const handleSubmit = async (e) => {
        e.preventDefault();
        const formData = new FormData();
        formData.append('csv_file', file);
        formData.append('input', JSON.stringify({
            sport_type: initialSportType,
            gender: initialGender,
            level: initialLevel
        }));

        try {
            const response = await fetch('http://localhost:8000/admin/', {
                method: 'POST',
                body: formData,
            });

            const data = await response.json();
            console.log('Response from server:', data);
        } catch (error) {
            console.error('Error uploading file:', error);
        }
    };

    return (
        <div>
            <form onSubmit={handleSubmit}>
                <input
                    type="file"
                    onChange={(e) => setFile(e.target.files[0])}
                    accept=".csv"
                    required
                />
                <button type="submit">Upload</button>
            </form>
        </div>
    );
};

export default UploadForm;
