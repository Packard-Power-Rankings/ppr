// src/components/admin/CsvTable.js
import React from 'react';
import './CsvTable.css';

const CSVTable = ({ headers, data, setData }) => {
  const handleCellChange = (rowIndex, fieldName, value) => {
    const updatedData = [...data];
    updatedData[rowIndex][fieldName] = value ? Number(value) : 0;
    setData(updatedData);
  };

  const headerLabels = {
    home_team_id: 'Home Team',
    original_home_score: 'Home Score',
    visitor_team_id: 'Away Team',
    original_visitor_score: 'Away Score'
  };

  // Filter out rows that don't have required IDs
  const filteredData = data.filter(row =>
    row['home_team_id'] && row['visitor_team_id']
  );

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
          {filteredData.map((row, rowIndex) => (
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
    </div>
  );
};

export default CSVTable;
