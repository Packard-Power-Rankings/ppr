// src/components/admin/CsvParser.js
import Papa from 'papaparse';

export const parseCsvFile = (file) => {
    return new Promise((resolve, reject) => {
        Papa.parse(file, {
            header: true,
            dynamicTyping: true,
            complete: (results) => resolve(results.data),
            error: (error) => reject(error.message),
        });
    });
};
