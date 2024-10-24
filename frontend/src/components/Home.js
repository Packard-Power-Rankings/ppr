// src/components/Home.js
import React from 'react';
import SportsRankings from './RankingTile.js';

const Home = () => {
    return (
        <div>
            <h2>Packard Power Rankings Home</h2>
            <p>Welcome to the Home Page!</p>
            <p>You can navigate to different sections of the app above.</p>
            <p>You can also view Power Rankings below.</p>

            <SportsRankings />
        </div>
    );
};

export default Home;
