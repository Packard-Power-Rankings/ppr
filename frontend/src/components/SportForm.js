// src/components/SportForm.js
import React, { useState, useEffect } from 'react';

const SportForm = ({ onSubmit, initialSportType = '', initialGender = '', initialLevel = '' }) => {
    const [sportType, setSportType] = useState(initialSportType);
    const [gender, setGender] = useState(initialGender);
    const [level, setLevel] = useState(initialLevel);

    // Update state when props change
    useEffect(() => {
        setSportType(initialSportType);
        setGender(initialGender);
        setLevel(initialLevel);
    }, [initialSportType, initialGender, initialLevel]);

    const handleSubmit = (e) => {
        e.preventDefault();
        // Make sure we call onSubmit only if it is passed as a prop
        if (typeof onSubmit === 'function') {
            onSubmit({ sportType, gender, level });
        } else {
            console.error('onSubmit is not a function');
        }
    };

    return (
        <form onSubmit={handleSubmit}>
            <div>
                <label htmlFor="sportType">Sport Type:</label>
                <select
                    id="sportType"
                    value={sportType}
                    onChange={(e) => setSportType(e.target.value)}
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
                    onChange={(e) => setGender(e.target.value)}
                >
                    <option value="">Select a gender</option>
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                </select>
            </div>

            <div>
                <label htmlFor="level">Level:</label>
                <select
                    id="level"
                    value={level}
                    onChange={(e) => setLevel(e.target.value)}
                >
                    <option value="">Select a level</option>
                    <option value="high_school">High School</option>
                    <option value="college">College</option>
                </select>
            </div>

            <button type="submit">Submit</button>
        </form>
    );
};

export default SportForm;
