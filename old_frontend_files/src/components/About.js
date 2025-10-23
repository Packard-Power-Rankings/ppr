// src/components/About.js
import React from 'react';

const About = () => {
    return (
        <div>
            <h2>About Page</h2>
            <p>Welcome to the About Page!</p>
            
            <h3>Algorithm History</h3>
            <p>
                The Packard Power Rankings algorithm was developed by Dr. Erik S. Packard while he was a student at Texas Tech University. Recent modifications have increased the computational complexity of the algorithm, resulting in lengthy execution times. With the help of Colorado Mesa University Computer Science students Drake Cullen, Nathan Briner, and Derric Loya, the time to enter data and compute rankings has decreased significantly.
            </p>

            <h3>About the Algorithm</h3>
            <p>
                The purpose of the program is to model how a person would rank teams if they could process all the information without bias. The algorithm utilizes game scores and considers home-field advantage. When two teams play, one team should move up in power while the other moves down by the same amount based on their performances relative to their current power ranking.
            </p>
            <p>
                In addition to the margin of victory, the algorithm takes the overall score into account to create a fair shift in a team’s power. For example, the difference between winning by 5 and 15 points is much larger than winning by 35 and 45 points. Although both games have the same margin of victory, a score of 35 to 45 is considered a more evenly matched game than one with a score of 5 to 15. Furthermore, a team could perform worse than expected and still increase in power if they win. For instance, if the program predicts a team should win by 6 points, but they only win by 3 points, they will still see an increase in power due to their significant chance of losing.
            </p>
            <p>
                When two teams play, their power scores can affect the rankings of their recent opponents, with the impact influenced by the recency of the game. For example, if the #10 ranked college football team’s last opponent performs much better than expected in their next game, the algorithm would increase the #10 team’s power by a fraction of their opponent’s change in power. If two teams with a wide power ranking face each other and the team projected to lose ends up winning, there will be a larger shift in rankings. Conversely, if a highly favored team wins, both teams will see minimal changes in their current power rankings.
            </p>
            <p>
                At the start of a season, the initial rankings are simply carried over from the end of the previous year. After scores are entered at the start of a new season, rankings will fluctuate until enough data has been gathered to assign appropriate rankings. Finally, the algorithm is applied several times over the season to achieve more accurate results.
            </p>

            <h3>Score Predictions</h3>
            <p>
                While the primary purpose of this website is to rank teams, it can also predict the score of a hypothetical game between two teams. These predictions are not definitive scores but decimal approximations of a possible game outcome. This is analogous to estimating that a family has 2.4 children: while such a prediction cannot be exact, an estimate of 2.4 may be more accurate than simply stating 2, despite 2 having a chance of being correct.
            </p>

            <h3>Z-Score</h3>
            <p>
                The z-score displayed on team pages measures the team’s performance in a game relative to the average performance across all games in a season and relies on the team's current power rankings. The score indicates how many standard deviations a team's performance is above or below average. A positive z-score means that the game improved that team’s ranking, while a negative one decreased it. The higher the z-score, the more it helps a team. At least 75% of the time, z-scores will be between -2 and 2; thus, if a z-score is greater than 2 or less than -2, that game had a significant impact. As more games are played, these z-scores will adjust as the program gains more information and recalibrates the scores accordingly. By analyzing z-scores, we can identify the best and worst games for a given team, helping determine the standout performances of the season.
            </p>

            <p>...</p>
        </div>
    );
};

export default About;
