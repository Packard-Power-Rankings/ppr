// src/components/admin/CsvTable.js
import React from 'react';

const CSVTable = ({ headers, data, setData }) => {
  const handleCellChange = (rowIndex, fieldName, value) => {
    const updatedData = [...data];
    updatedData[rowIndex][fieldName] = value;
    setData(updatedData);
  };

  // Filter the headers to only include the relevant fields (team names and scores)
  const filteredHeaders = headers.filter(header =>
    header === 'home_team_id' || header === 'visitor_team_id' ||
    header === 'original_home_score' || header === 'original_visitor_score'
  );

  return (
    <table>
      <thead>
        <tr>
          {filteredHeaders.map((header, idx) => (
            <th key={idx}>{header}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {data.map((row, rowIndex) => (
          <tr key={rowIndex}>
            {filteredHeaders.map((field, cellIndex) => {
              // Editable fields for the scores
              if (field === 'original_home_score' || field === 'original_visitor_score') {
                return (
                  <td key={cellIndex}>
                    <input
                      type="number"
                      value={row[field] || ''}
                      onChange={(e) =>
                        handleCellChange(rowIndex, field, e.target.value)
                      }
                    />
                  </td>
                );
              }

              // Non-editable team names
              if (field === 'home_team_id' || field === 'visitor_team_id') {
                return (
                  <td key={cellIndex}>
                    {row[field]}
                  </td>
                );
              }

              return null; // If it's not one of the desired fields, return nothing
            })}
          </tr>
        ))}
      </tbody>
    </table>
  );
};

export default CSVTable;
