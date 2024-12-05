// src/components/admin/RunAlgorithm.js
import React, { useState } from 'react';

const RunAlgorithm = ({ onRun, sportType, gender, level }) => {
    const [runCount, setRunCount] = useState(1);
    const [errorMessage, setErrorMessage] = useState('');

    const handleRunAlgorithm = async () => {
        if (runCount < 1 || runCount > 30) {
            setErrorMessage('Please enter a value between 1 and 30.');
            return;
        }

        const token = localStorage.getItem('access_token');
        if (!token) {
            setErrorMessage('Unauthorized: No token found');
            return;
        }

        const formData = new FormData();
        formData.append('sport_type', sportType);
        formData.append('gender', gender);
        formData.append('level', level);
        formData.append('iterations', runCount);

        try {
            const response = await fetch(`http://localhost:8000/run_algorithm/`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    // Do not set 'Content-Type'; fetch will set it automatically for FormData
                },
                body: formData,
            });

            const data = await response.json();

            if (!response.ok) {
                setErrorMessage(data.detail || 'An error occurred');
                throw new Error('Error running algorithm');
            }

            console.log('Algorithm run successful:', data);
            if (onRun) onRun(data);
        } catch (error) {
            setErrorMessage('There was an issue with your request.');
            console.error('Fetch Error:', error);
        }
    };

    return (
        <div>
            <input
                type="number"
                placeholder="Number of Times to Run (1-30)"
                value={runCount}
                onChange={(e) => setRunCount(Math.max(1, Math.min(30, e.target.value)))}
                min="1"
                max="30"
            />
            <button onClick={handleRunAlgorithm}>Run Algorithm</button>
            {errorMessage && <p style={{ color: 'red' }}>{errorMessage}</p>}
        </div>
    );
};

export default RunAlgorithm;
