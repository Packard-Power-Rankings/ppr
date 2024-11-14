// src/components/admin/UploadForm.js
import React, { useState } from 'react';
import UpdateTeam from './UpdateTeam';
import RunAlgorithm from './RunAlgorithm';
import CsvUpload from './CsvUpload';

const UploadForm = ({ initialSportType, initialGender, initialLevel }) => {
    const [missingTeams, setMissingTeams] = useState([]);
    const [showUpdateForm, setShowUpdateForm] = useState(false);
    const [isUploadDisabled, setIsUploadDisabled] = useState(false);
    const [errorMessage, setErrorMessage] = useState('');

    const handleUploadComplete = (teams) => {
        setMissingTeams(teams);
        setShowUpdateForm(true);
        setIsUploadDisabled(true); // Disable upload buttons after successful upload
    };

    const getToken = () => {
        // Get the JWT token from localStorage
        return localStorage.getItem('access_token');
      };
      
      const handleUpdateSubmit = async (teams) => {
          const token = getToken();
          if (!token) {
              setErrorMessage('Unauthorized: No token found');
              return;
          }
      
          const formData = new FormData();
          formData.append('teams', JSON.stringify(teams));
      
          try {
              const response = await fetch('http://localhost:8000/admin/add_teams/', {
                  method: 'POST',
                  headers: {
                      'Authorization': `Bearer ${token}`,  // Include the token here
                  },
                  body: formData,
              });
      
              if (!response.ok) {
                  const errorData = await response.json();
                  setErrorMessage(errorData.detail || 'Submission failed.');
                  throw new Error(`Fetch error: ${response.statusText}`);
              }
      
              setErrorMessage('');
          } catch (error) {
              setErrorMessage('There was an issue with your request.');
          }
      };      

      const handleRunAlgorithm = async (runCount) => {
        const token = getToken();
        if (!token) {
            setErrorMessage('Unauthorized: No token found');
            return;
        }
    
        const formData = new FormData();
        formData.append('sport_type', initialSportType);
        formData.append('gender', initialGender);
        formData.append('level', initialLevel);
    
        try {
            const response = await fetch(`http://localhost:8000/admin/run_algorithm/?iterations=${runCount}`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,  // Include the token here
                },
                body: formData,
            });
    
            const data = await response.json();
    
            if (!response.ok) {
                setErrorMessage(data.detail || 'An error occurred');
                throw new Error('Error running algorithm');
            }
    
            console.log('Algorithm run successful:', data);
        } catch (error) {
            setErrorMessage('There was an issue with your request.');
            console.error('Fetch Error:', error);
        }
    };    

    return (
        <div>
            {/* CSV Upload Section */}
            <div style={{ marginBottom: '20px' }}>
                <CsvUpload
                    initialSportType={initialSportType}
                    initialGender={initialGender}
                    initialLevel={initialLevel}
                    onUploadComplete={handleUploadComplete}
                    isUploadDisabled={isUploadDisabled}
                />
            </div>

            {/* Display error message if any */}
            {errorMessage && <p style={{ color: 'red' }}>{errorMessage}</p>}

            {/* Update Teams Section (conditionally shown) */}
            {showUpdateForm && (
                <div style={{ marginBottom: '20px' }}>
                    <UpdateTeam
                        initialTeams={missingTeams.map((team) => ({
                            team_name: team,
                            score: '',
                            power_ranking: '',
                            division: '',
                            conference: '',
                            state: '',
                        }))}
                        onUpdateSubmit={handleUpdateSubmit}
                    />
                </div>
            )}

            {/* Run Algorithm Section */}
            <div style={{ borderTop: '1px solid #ccc', paddingTop: '20px' }}>
                <RunAlgorithm onRun={handleRunAlgorithm} />
            </div>
        </div>
    );
};

export default UploadForm;
