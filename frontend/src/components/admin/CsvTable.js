// src/components/admin/CsvTable.js
import React, { useState, useEffect } from 'react';
import './CsvTable.css';

const CSVTable = ({ headers, data, setData, onTableComplete = () => { } }) => { // Default empty function
  const [currentPage, setCurrentPage] = useState(1);
  const rowsPerPage = 10;

  const handleCellChange = (rowIndex, fieldName, value) => {
    const updatedData = [...data];
    updatedData[rowIndex][fieldName] = value ? Number(value) : 0;
    setData(updatedData);
  };

  // Check if the table is complete (all required fields are filled)
  useEffect(() => {
    const isComplete = data.every((row) =>
      row['original_home_score'] !== undefined && row['original_visitor_score'] !== undefined
    );
    onTableComplete(isComplete); // Notify parent component
  }, [data, onTableComplete]);

  const headerLabels = {
    home_team_id: 'Home Team',
    original_home_score: 'Home Score',
    visitor_team_id: 'Away Team',
    original_visitor_score: 'Away Score'
  };

  const filteredData = data.filter(row =>
    row['home_team_id'] && row['visitor_team_id']
  );

  const indexOfLastRow = currentPage * rowsPerPage;
  const indexOfFirstRow = indexOfLastRow - rowsPerPage;
  const currentRows = filteredData.slice(indexOfFirstRow, indexOfLastRow);

  const paginate = (pageNumber) => setCurrentPage(pageNumber);

  const totalPages = Math.ceil(filteredData.length / rowsPerPage);

  return (
    <div className="csv-table-container">
      <table className="csv-table">
        <thead>
          <tr className="table-header">
            <th>{headerLabels['home_team_id']}</th>
            <th>{headerLabels['original_home_score']}</th>
            <th>{headerLabels['visitor_team_id']}</th>
            <th>{headerLabels['original_visitor_score']}</th>
          </tr>
        </thead>
        <tbody>
          {currentRows.map((row, rowIndex) => (
            <tr key={rowIndex} className="team-row">
              <td>{row['home_team_id'] || '-'}</td>
              <td>
                <input
                  type="number"
                  value={row['original_home_score'] ?? 0}
                  onChange={(e) => handleCellChange(rowIndex, 'original_home_score', e.target.value)}
                />
              </td>
              <td>{row['visitor_team_id'] || '-'}</td>
              <td>
                <input
                  type="number"
                  value={row['original_visitor_score'] ?? 0}
                  onChange={(e) => handleCellChange(rowIndex, 'original_visitor_score', e.target.value)}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="pagination">
        <button onClick={() => paginate(currentPage - 1)} disabled={currentPage === 1}>
          Previous
        </button>
        {Array.from({ length: totalPages }, (_, index) => (
          <button
            key={index}
            className={currentPage === index + 1 ? 'active' : ''}
            onClick={() => paginate(index + 1)}
          >
            {index + 1}
          </button>
        ))}
        <button onClick={() => paginate(currentPage + 1)} disabled={currentPage === totalPages}>
          Next
        </button>
      </div>
    </div>
  );
};

export default CSVTable;
