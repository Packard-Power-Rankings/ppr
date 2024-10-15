// src/components/Home.js
import React from 'react';
import { Link } from 'react-router-dom';
import RankingTile from './RankingTile'; // Import the RankingTile component
import './Home.css'; // Create a CSS file for Home page styles

const Home = () => {
    return (
        <div>
            <h2>Packard Power Rankings Home</h2>
            <p>Welcome to the Home Page!</p>
            <p>You can navigate to different sections of the app above.</p>
            <p>You can also view Power Rankings below.</p>

            <div className="ranking-tiles">
                <RankingTile title="High School Women's Basketball Ranking" link="/womens-basketball-ranking" />
                <RankingTile title="High School Men's Basketball Ranking" link="/mens-basketball-ranking" />
                <RankingTile title="High School Football Ranking" link="/hs-football-ranking" />
                <RankingTile title="College Men's Basketball Ranking" link="/mens-college-basketball-ranking" />
                <RankingTile title="College Women's Basketball Ranking" link="/womens-college-basketball-ranking" />
                <RankingTile title="College Football Ranking" link="/college-football-ranking" />
            </div>
        </div>
    );
};

export default Home;
