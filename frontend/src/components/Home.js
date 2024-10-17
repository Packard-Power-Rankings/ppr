// src/components/Home.js
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import RankingTile from './RankingTile'; // Import the RankingTile component
import './Home.css'; // Create a CSS file for Home page styles

const Home = () => {
    // Define state for each ranking
    const [collegeFootballRanking, setCollegeFootballRanking] = useState(null);
    const [hsFootballRanking, setHsFootballRanking] = useState(null);
    const [mensCollegeBasketballRanking, setMensCollegeBasketballRanking] = useState(null);
    const [womensCollegeBasketballRanking, setWomensCollegeBasketballRanking] = useState(null);
    const [womensBasketballRanking, setWomensBasketballRanking] = useState(null);
    const [mensBasketballRanking, setMensBasketballRanking] = useState(null);

    // Fetch data from the backend when the component mounts
    useEffect(() => {
        // Fetch rankings data from the respective FastAPI endpoints
        fetch('http://localhost:8000/college-football/')
            .then(response => response.json())
            .then(data => setCollegeFootballRanking(data))
            .catch(error => console.error('Error fetching college football ranking:', error));

        fetch('http://localhost:8000/hs-football/')
            .then(response => response.json())
            .then(data => setHsFootballRanking(data))
            .catch(error => console.error('Error fetching high school football ranking:', error));

        fetch('http://localhost:8000/mens-college-basketball/')
            .then(response => response.json())
            .then(data => setMensCollegeBasketballRanking(data))
            .catch(error => console.error('Error fetching men\'s college basketball ranking:', error));

        fetch('http://localhost:8000/womens-college-basketball/')
            .then(response => response.json())
            .then(data => setWomensCollegeBasketballRanking(data))
            .catch(error => console.error('Error fetching women\'s college basketball ranking:', error));

        fetch('http://localhost:8000/womens-basketball/')
            .then(response => response.json())
            .then(data => setWomensBasketballRanking(data))
            .catch(error => console.error('Error fetching high school women\'s basketball ranking:', error));

        fetch('http://localhost:8000/mens-basketball/')
            .then(response => response.json())
            .then(data => setMensBasketballRanking(data))
            .catch(error => console.error('Error fetching high school men\'s basketball ranking:', error));
    }, []);  // Empty array ensures this runs once when the component mounts

    return (
        <div>
            <h2>Packard Power Rankings Home</h2>
            <p>Welcome to the Home Page!</p>
            <p>You can navigate to different sections of the app above.</p>
            <p>You can also view Power Rankings below.</p>

            <div className="ranking-tiles">
                {/* Pass the fetched rankings as props to the RankingTile components */}
                <RankingTile title="College Football Ranking" link="/college-football-ranking" data={collegeFootballRanking} />
                <RankingTile title="High School Football Ranking" link="/hs-football-ranking" data={hsFootballRanking} />
                <RankingTile title="College Men's Basketball Ranking" link="/mens-college-basketball-ranking" data={mensCollegeBasketballRanking} />
                <RankingTile title="College Women's Basketball Ranking" link="/womens-college-basketball-ranking" data={womensCollegeBasketballRanking} />
                <RankingTile title="High School Women's Basketball Ranking" link="/womens-basketball-ranking" data={womensBasketballRanking} />
                <RankingTile title="High School Men's Basketball Ranking" link="/mens-basketball-ranking" data={mensBasketballRanking} />
            </div>
        </div>
    );
};

export default Home;
