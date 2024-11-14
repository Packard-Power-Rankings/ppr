// src/components/admin/DeleteForm.js
import React, { useState } from 'react';
import DeleteSeason from './DeleteSeason';

const DeleteForm = ({ seasonName, onComplete }) => {
    // Set initial state to an empty string
    const [deleteOption, setDeleteOption] = useState('');

    const handleOptionChange = (e) => {
        setDeleteOption(e.target.value);
    };

    const renderDeleteOperation = () => {
        switch (deleteOption) {
            case 'deleteSeason':
                return <DeleteSeason seasonName={seasonName} onComplete={onComplete} />;
            // Future delete options can be added here
            default:
                return null;
        }
    };

    return (
        <div>
            <select onChange={handleOptionChange} value={deleteOption}>
                <option value="">Select an option</option>
                <option value="deleteSeason">Delete Season</option>
                {/* Additional delete options can be added here */}
            </select>

            {renderDeleteOperation()}

            {/* Single Cancel button that applies to all delete options */}
            {deleteOption && <button onClick={onComplete}>Cancel</button>}
        </div>
    );
};

export default DeleteForm;
