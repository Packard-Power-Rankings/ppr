import React, { useEffect, useState } from 'react';

const ThemeToggle = () => {
    const [isDarkTheme, setIsDarkTheme] = useState(false);

    // Effect to apply the user's theme preference from localStorage
    useEffect(() => {
        const savedTheme = localStorage.getItem('theme');
        const prefersDark = savedTheme === 'dark' || (savedTheme === null && window.matchMedia('(prefers-color-scheme: dark)').matches);
        
        setIsDarkTheme(prefersDark);
        document.documentElement.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
    }, []);

    // Function to toggle the theme and save to localStorage
    const toggleTheme = () => {
        setIsDarkTheme(prevTheme => {
            const newTheme = !prevTheme;
            document.documentElement.setAttribute('data-theme', newTheme ? 'dark' : 'light');
            localStorage.setItem('theme', newTheme ? 'dark' : 'light'); // Save theme to localStorage
            return newTheme;
        });
    };

    return (
        <button onClick={toggleTheme}>
            Switch to {isDarkTheme ? 'Light' : 'Dark'} Theme
        </button>
    );
};

export default ThemeToggle;
