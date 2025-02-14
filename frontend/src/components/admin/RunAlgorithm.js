// src/components/admin/RunAlgorithm.js
import React, { useState } from 'react';

const RunAlgorithm = ({ sportType, gender, level }) => {
    const [runCount, setRunCount] = useState(1);
    const [errorMessage, setErrorMessage] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);

    const getToken = () => {
        return localStorage.getItem('access_token');
    };

    const handleAuthError = (response) => {
        if (response.status === 401) {
            localStorage.removeItem('access_token'); // Clear expired token
            window.location.href = '/login'; // Redirect to login page
        } else {
            response.text().then((text) => {
                setErrorMessage(text || 'An error occurred. Please try again.');
            });
        }
    };

    const handleRunAlgorithm = async () => {
        if (runCount < 1 || runCount > 30) {
            setErrorMessage('Please enter a value between 1 and 30.');
            return;
        }

        const token = getToken();
        if (!token) {
            setErrorMessage('Unauthorized: No token found');
            window.location.href = '/login'; // Redirect to login page
            return;
        }

        const params = new URLSearchParams();
        params.append('sport_type', sportType);
        params.append('gender', gender);
        params.append('level', level);
        params.append('iterations', runCount);

        setIsSubmitting(true); // Disable the button while submitting

        try {
            const response = await fetch(`http://localhost:8000/run_algorithm/?${params.toString()}`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: params.toString(),
            });

            if (response.ok) {
                const data = await response.json();
                console.log('Algorithm run successful:', data);
            } else {
                handleAuthError(response);
            }
        } catch (error) {
            setErrorMessage('There was an issue with the algorithm request. Please try again.');
            console.error('Fetch Error:', error);
        } finally {
            setIsSubmitting(false); // Re-enable the button
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
            <button onClick={handleRunAlgorithm} disabled={isSubmitting}>Run Algorithm</button>
            {errorMessage && <p style={{ color: 'red' }}>{errorMessage}</p>}
        </div>
    );
};

export default RunAlgorithm;
