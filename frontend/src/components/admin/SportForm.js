// src/components/admin/SportForm.js
import React, { useState, useEffect } from 'react';

const SportForm = ({ onSubmit, initialSportType = '', initialGender = '', initialLevel = '' }) => {
    const [sportType, setSportType] = useState(initialSportType);
    const [gender, setGender] = useState(initialGender);
    const [level, setLevel] = useState(initialLevel);
    const [errorMessage, setErrorMessage] = useState(''); // To display error messages

    // Update state when props change
    useEffect(() => {
        setSportType(initialSportType);
        setGender(initialGender);
        setLevel(initialLevel);
    }, [initialSportType, initialGender, initialLevel]);

    const handleSubmit = (e) => {
        e.preventDefault();
        // Check if all fields are filled
        if (!sportType || !gender || !level) {
            setErrorMessage('Please fill in all fields.'); // Show error if fields are missing
            return; // Prevent form submission
        }
        
        // Make sure we call onSubmit only if it is passed as a prop
        if (typeof onSubmit === 'function') {
            onSubmit({ sportType, gender, level });
        } else {
            console.error('onSubmit is not a function');
        }
    };

    const handleSportTypeChange = (e) => {
        const selectedSportType = e.target.value;
        setSportType(selectedSportType);

        // Auto-select 'Mens' only for Football
        if (selectedSportType === 'football') {
            setGender('mens');
        } else if (selectedSportType === 'basketball') {
            setGender(''); // Reset gender for Basketball
        } else {
            setGender(''); // Reset gender for any other sport type
        }
    };

    const handleGenderChange = (e) => {
        setGender(e.target.value);
    };

    const isLevelDisabled = !(sportType && gender); // Level is disabled if sport type or gender is not selected

    return (
        <form onSubmit={handleSubmit}>
            <div>
                <label htmlFor="sportType">Sport Type:</label>
                <select
                    id="sportType"
                    value={sportType}
                    onChange={handleSportTypeChange}
                    required // Make this field required
                >
                    <option value="">Select a sport type</option>
                    <option value="football">Football</option>
                    <option value="basketball">Basketball</option>
                </select>
            </div>

            <div>
                <label htmlFor="gender">Gender:</label>
                <select
                    id="gender"
                    value={gender}
                    onChange={handleGenderChange}
                    disabled={sportType === ''} // Disable until a sport is selected
                    required // Make this field required
                >
                    <option value="">Select a gender</option>
                    <option value="mens">Mens</option>
                    {sportType === 'basketball' && <option value="womens">Womens</option>}
                </select>
            </div>

            <div>
                <label htmlFor="level">Level:</label>
                <select
                    id="level"
                    value={level}
                    onChange={(e) => setLevel(e.target.value)}
                    disabled={isLevelDisabled} // Disable until both sport type and gender are selected
                    required // Make this field required
                >
                    <option value="">Select a level</option>
                    <option value="high_school">High School</option>
                    <option value="college">College</option>
                </select>
            </div>

            {errorMessage && <p style={{ color: 'red' }}>{errorMessage}</p>} {/* Show error message if needed */}

            <button type="submit">Select Sport</button>
        </form>
    );
};

export default SportForm;
