// src/components/RankingTile.js
import React from 'react';
import './RankingTile.css'; // Create a CSS file for styling

const RankingTile = ({ title, link }) => {
    return (
        <div className="ranking-tile">
            <h3>{title}</h3>
            <a href={link} className="tile-link">View Rankings</a>
        </div>
    );
};

export default RankingTile;
