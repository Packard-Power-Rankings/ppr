// src/components/admin/DeleteForm.js
import React, { useState } from 'react';
import DeleteSeason from './DeleteSeason';

const DeleteForm = ({ seasonName, onComplete }) => {
    // Set initial state to an empty string
    const [deleteOption, setDeleteOption] = useState('');

    const handleOptionChange = (e) => {
        setDeleteOption(e.target.value);
    };

    const handleCancel = () => {
        setDeleteOption(''); // Reset the delete option to hide delete form
        if (onComplete && typeof onComplete === 'function') {
            onComplete(); // Call onComplete if it's a valid function
        }
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
                <option value="deleteSeason">New Season</option>
                {/* Additional delete options can be added here */}
            </select>

            {renderDeleteOperation()}

            {/* Single Cancel button that applies to all delete options */}
            {deleteOption && <button onClick={handleCancel}>Cancel</button>}
        </div>
    );
};

export default DeleteForm;
