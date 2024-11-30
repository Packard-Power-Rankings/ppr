// src/components/admin/CsvParser.js
import Papa from 'papaparse';

export const parseCsvFile = (file) => {
    return new Promise((resolve, reject) => {
        Papa.parse(file, {
            header: true,              // Keep header as key
            dynamicTyping: true,       // Automatically type cast values
            skipEmptyLines: true,      // Skip any empty lines in the file
            encoding: 'UTF-8',         // Ensure proper encoding (optional)
            delimiter: ',',            // Explicitly set the delimiter to comma
            complete: (results) => {
                if (results.errors.length > 0) {
                    // Log detailed parsing errors for debugging
                    console.error('CSV parsing errors:', results.errors);
                    reject('There was an issue with the CSV format.');
                } else if (results.data.length === 0) {
                    reject('CSV file is empty or has no valid data.');
                } else {
                    console.log('CSV parsed successfully:', results.data);
                    resolve(results.data); // Successfully parsed data
                }
            },
            error: (error) => {
                // Log error message for further debugging
                console.error('Parsing error:', error);
                reject(`Parsing error: ${error.message}`);
            },
        });
    });
};
