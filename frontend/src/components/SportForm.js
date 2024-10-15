// src/components/SportForm.js
import React, { useState } from 'react';

const SportForm = () => {
    const [sportType, setSportType] = useState('');
    const [gender, setGender] = useState('');
    const [level, setLevel] = useState('');

    const handleSubmit = (e) => {
        e.preventDefault();
        console.log({
            sportType,
            gender,
            level,
        });
        // Here, you can implement the logic to handle the data
        // or send it to the backend when you're ready.
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
                    {/* Add more options as needed */}
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
