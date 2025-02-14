import React from 'react';
import { Link } from 'react-router-dom';
import './RankingTile.css';

const RankingTile = () => {
    const footballSports = [
        {
            title: 'College Football',
            link: '/football/mens/college',
        },
        {
            title: 'Colorado High School Football',
            link: '/football/mens/high-school',
        },
    ];

    const basketballSports = [
        {
            title: 'Men’s College Basketball',
            link: '/basketball/mens/college',
        },
        {
            title: 'Women’s College Basketball',
            link: '/basketball/womens/college',
        },
        {
            title: 'Colorado Boy’s High School Basketball',
            link: '/basketball/mens/high-school',
        },
        {
            title: 'Colorado Girl’s High School Basketball',
            link: '/basketball/womens/high-school',
        },
    ];

    return (
        <div className="ranking-tiles">
            {/* Row for football tiles */}
            <div className="tile-row">
                {footballSports.map((sport, index) => (
                    <div key={index} className="ranking-tile">
                        <h3>{sport.title}</h3>
                        <Link to={sport.link} className="tile-link">
                            View Power Rankings
                        </Link>
                    </div>
                ))}
            </div>

            {/* Row for basketball tiles */}
            <div className="tile-row">
                {basketballSports.map((sport, index) => (
                    <div key={index} className="ranking-tile">
                        <h3>{sport.title}</h3>
                        <Link to={sport.link} className="tile-link">
                            View Power Rankings
                        </Link>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default RankingTile;
