// src/components/Home.js
import React from 'react';
import RankingTile from './RankingTile.js';

const Home = () => {
    return (
        <div>
            <h2>Packard Power Rankings Home Page</h2>
            <p>Welcome to the Home Page!</p>
            <p>You can navigate to different sections of the app above.</p>
            <h3>Power Rankings</h3>
            <p>View the Power Rankings below.</p>

            <RankingTile />
        </div>
    );
};

export default Home;
