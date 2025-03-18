import React from "react";
import { 
    CCol,
    CContainer,
    CImage,
    CRow,
} from "@coreui/react";

import ErikPackard from '../../../assets/images/ErikPackard.png';
import RamBasnet from '../../../assets/images/RamBasnet.png';
import DerricLoya from '../../../assets/images/DerricLoya.png';
import DrakeCullen from '../../../assets/images/DrakeCullen.png';
import NateBriner from '../../../assets/images/NateBriner.png';

const About = () => {
    return (
        <CContainer className="mt-4">
            <section className="mb-5">
                <h2>Algorithm History</h2>
                <p>The Packard Power Rankings algorithm was developed by Dr. Erik S. Packard while he was a student at Texas Tech University. Recent modifications have increased the computation complexity of the algorithm resulting in lengthy execution time. Now, with the help of Colorado Mesa University Computer Science students Drake Cullen, Nathan Briner, and Derric Loya, the time to enter data compute rankings has decreased greatly.</p>
            </section>
            <section className="mb-5">
                <h2>About the Algorithm</h2>
                <p>The idea of the program is to model how a person would rank teams if they could process all the information and have no bias. The algorithm utilizes game scores and considers home-field advantage. When two teams play, one team should move up in power and the other down by the same amount based on their performances in relation to their current power ranking. In addition to the margin of victory, the algorithm considers the overall score in a game to create a more fair shift in a team’s power. For example, the difference between winning by 5 and 15 is much larger than the difference between winning by 35 and 45. In both games, the margin of victory is the same; however, 35 to 45 is considered a more even game than 5 to 15. It is also the case that a team could do worse than expected and still increase in power if they win. For instance, if the program predicts a team should win by 6 points and they only win by 3 points, they will still improve in power because they had a significant chance of losing. </p>
                <p>Two teams that have recently played will affect the power scores of their other recent opponents. The effect on an opponent's power is influenced by the recency of the game. For example, if the #10 ranked college football team’s last opponent did much better than expected in their next game, the algorithm would increase the #10 team’s power by a fraction of their opponent’s change in power. If two teams with a wide power ranking play each other, and the team projected to lose ends up winning, there will be a much larger shift in rankings. Similarly, in the case that a highly favored team wins, both teams will see minimal change in their current power. For a team to move up in the rankings, they will need to perform well in their games, and their connected opponents will also have to perform well in their games. </p>
                <p>At the start of a season, the initial rankings are simply the rankings from the end of the previous year. After scores are entered at the start of a new season, the rankings will fluctuate until enough data has been gathered and their appropriate ranking has been assigned. Finally, the algorithm is repeated several times over a season to achieve more accurate results.</p>
            </section>
            <section className="mb-5">
                <h2>Score Predictions</h2>
                <p>While the primary purpose of this website is to rank teams, it also can predict the score of a hypothetical game played by two teams. The predictions are not meant to be considered definite scores, but decimal approximations of a hypothetical game outcome. This is analogous to guessing that a family has 2.4 children. Such a prediction cannot be correct, but an estimate of 2.4 might be a better estimate than 2, despite 2 having a chance of being exact.</p>
            </section>
            <section className="mb-5">
                <h2>Z-Score</h2>
                <p>The z-score displayed on team pages measures the team’s performance in a game when considering the average performance across all games in a season and relies on the teams current power rankings. The score itself conveys how many standard deviations above or below the average game performance the team did in that game. A positive z-scores means that the game improved that team’s ranking and a negative one decreased it. The higher the z-score the more it helps a team. At least 75% of the time the z-score will be between -2 and 2, so if a z-score is greater than 2 or less than -2, that game was greatly impactful. After more games are played, these z-scores will change as the program will have more information and curve the z-scores up or down given the new information. With the z-scores, you can tell which games were the best and worst for a given team as viewed by the program. By looking at z-scores, we can decide which game was the best in the season.</p>
            </section>
            <section className="mb-5">
                <h2>Creator</h2>
                <CRow className="align-items-center">
                    <CCol md={3} className="text-center">
                        <CImage rounded thumbnail src={ErikPackard} width={200} height={200}/>
                    </CCol>
                    <CCol md={9}>
                        <h5>Erik Packard</h5>
                        <p>Dr. Erik S. Packard is an Associate Professor of Mathematics at Colorado Mesa University in Grand Junction, Colorado. He obtained a B.S., M.S., and Ph.D. from Texas Tech University. As a mathematician, his specialty is in pure mathematics; however, sports modeling has motivated him to venture into the realm of applied mathematics. Besides mathematics, Dr. Packard’s interests include distance running, mountaineering, music, and cats. In his 40’s he sported a 5K time of 15:36 and a 10K time of 33:09. Although serious running is most likely in his past, he still is an avid mountaineer. He has climbed over 2000 peaks in Colorado and 1000 peaks in Utah.</p>
                    </CCol>
                </CRow>
            </section>
            <section className="mb-5">
                <h2>Current Maintainer</h2>
                <CRow className="align-items-center">
                    <CCol md={3} className="text-center">
                        <CImage rounded thumbnail src={RamBasnet} width={200} height={200}/>
                    </CCol>
                    <CCol md={9}>
                        <h5>Ram Basnet</h5>
                        <p>Ram Basnet loves many sports most importantly soccer and basketball. Ram grew up playing basketball, soccer and volleyball for his high school teams. He continues to play soccer in Grand Valley soccer league.</p>
                        <p>Ram received his M.S., and Ph.D. in Computer Science from New Mexico Tech. He is currently employed as an associate professor of Computer Science at Colorado Mesa University.</p>
                    </CCol>
                </CRow>
            </section>
            <section className="mb-5">
                <h2>Previous Team Members</h2>
                {
                    [
                        { img: DerricLoya, name: 'Derric Loya', desc: "Derric Loya graduated from Colorado Mesa University with a Bachelor of Science in Computer Science, with a Web Application Development Professional Certificate. During which, Derric held the position of Vice President and was a founding member of the Society of Hispanic Professional Engineers at CMU. Additionally, being honored as a member of Upsilon Pi Epsilon (the International Honor Society for Computing and Informatics) and Kappa Mu Epsilon (the National Mathematics Honor Society)." },
                        { img: DrakeCullen, name: 'Drake Cullen', desc: "Drake Cullen is currently pursuing a Bachelor’s degree in Computer Science with minors in Cybersecurity and Mathematics at Colorado Mesa University. He is the former President of the Cybersecurity Club, the President of Upsilon Pi Epsilon (the International Honor Society for Computing and Informatics) and the Treasurer of Kappa Mu Epsilon (the National Mathematics Honor Society) at CMU." },
                        { img: NateBriner, name: 'Nate Briner', desc: "Nathan Briner is currently pursuing a Bachelor’s degree in Computer Science and a minor in Mathematics at Colorado Mesa University. He is also a Vice President of CMU's Computer Science Club and Vice President of Upsilon Pi Epsilon (the International Honor Society for Computing and Informatics) at CMU." }
                    ].map((member, index) => (
                        <CRow className="align-items-center mb-4" key={index}>
                            <CCol md={3} className="text-center">
                                <CImage rounded thumbnail src={member.img} width={200} height={200}/>
                            </CCol>
                            <CCol md={9}>
                                <h5>{member.name}</h5>
                                <p>{member.desc}</p>
                            </CCol>
                        </CRow>
                    ))
                }
            </section>
        </CContainer>
    )
}

export default About
