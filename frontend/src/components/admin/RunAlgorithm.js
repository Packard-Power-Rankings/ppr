// src/components/admin/RunAlgorithm.js
import React, { useState } from 'react';

const RunAlgorithm = ({ onRun }) => {
    const [runCount, setRunCount] = useState(1);
    const [errorMessage, setErrorMessage] = useState('');

    const handleRunAlgorithm = async () => {
        if (runCount < 1 || runCount > 30) {
            setErrorMessage('Please enter a value between 1 and 30.');
            return;
        }

        try {
            await onRun(runCount);
            setErrorMessage('');
        } catch (error) {
            console.error('Error running algorithm:', error);
            setErrorMessage('There was an issue running the algorithm.');
        }
    };

    return (
        <div>
            <h2>Run Algorithm</h2>
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
