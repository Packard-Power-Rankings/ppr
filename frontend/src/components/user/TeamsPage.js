import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import './TeamsPage.css';

const TeamsPage = () => {
    const { sportType } = useParams();
    const [teams, setTeams] = useState([]);
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState("");
    const [sortColumn, setSortColumn] = useState(null);
    const [sortOrder, setSortOrder] = useState("asc");
    const [currentPage, setCurrentPage] = useState(1);
    const [teamsPerPage] = useState(50);
    const [selectedDivision, setSelectedDivision] = useState("");
    const [selectedConference, setSelectedConference] = useState("");
    const [divisions, setDivisions] = useState([]);
    const [conferences, setConferences] = useState([]);

    const fetchTeams = async () => {
        setLoading(true);
        try {
            const response = await fetch(`http://localhost:8000/user/${sportType}/?gender=mens&level=college`);
            if (!response.ok) {
                throw new Error(`${response.status} (HTTP not found)`);
            }
            const data = await response.json();
            if (data.data && Array.isArray(data.data.teams)) {
                setTeams(data.data.teams);
                setDivisions([...new Set(data.data.teams.map(team => team.division).filter(Boolean))]);
                setConferences([...new Set(data.data.teams.map(team => team.conference).filter(Boolean))]);
            } else {
                setTeams([]);
                throw new Error('Expected an array of teams');
            }
        } catch (err) {
            console.error(err);
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchTeams();
    }, [sportType]);

    const applySortingAndFiltering = () => {
        let filteredTeams = teams.filter((team) => {
            return team.team_name.toLowerCase().includes(searchQuery.toLowerCase());
        });

        if (selectedDivision) {
            filteredTeams = filteredTeams.filter(team => team.division === selectedDivision);
        }

        if (selectedConference) {
            filteredTeams = filteredTeams.filter(team => team.conference === selectedConference);
        }

        return filteredTeams.sort((a, b) => {
            if (!sortColumn) return 0;
            const valA = a[sortColumn];
            const valB = b[sortColumn];

            if (valA == null || valB == null) return 0;
            if (sortOrder === "asc") return valA > valB ? 1 : -1;
            else return valA < valB ? 1 : -1;
        });
    };

    const handleSearchChange = (e) => {
        setSearchQuery(e.target.value);
    };

    const handleSort = (column) => {
        const order = (sortColumn === column && sortOrder === "asc") ? "desc" : "asc";
        setSortColumn(column);
        setSortOrder(order);
    };

    const handleDivisionChange = (e) => {
        setSelectedDivision(e.target.value);
    };

    const handleConferenceChange = (e) => {
        setSelectedConference(e.target.value);
    };

    const indexOfLastTeam = currentPage * teamsPerPage;
    const indexOfFirstTeam = indexOfLastTeam - teamsPerPage;
    const currentTeams = applySortingAndFiltering().slice(indexOfFirstTeam, indexOfLastTeam);

    const totalPages = Math.ceil(applySortingAndFiltering().length / teamsPerPage);

    const handlePageChange = (pageNumber) => {
        setCurrentPage(pageNumber);
        window.scrollTo(0, 0);  // Scroll to the top of the page
    };

    if (loading) return <p>Loading...</p>;
    if (error) return <p>Error: {error}</p>;

    return (
        <div>
            <h2>{sportType.charAt(0).toUpperCase() + sportType.slice(1)} Teams</h2>

            <input
                type="text"
                placeholder="Search teams..."
                value={searchQuery}
                onChange={handleSearchChange}
                className="search-input"
            />

            <div className="filters">
                <select onChange={handleDivisionChange} value={selectedDivision}>
                    <option value="">All Divisions</option>
                    {divisions.map((division, index) => (
                        <option key={index} value={division}>{division}</option>
                    ))}
                </select>

                <select onChange={handleConferenceChange} value={selectedConference}>
                    <option value="">All Conferences</option>
                    {conferences.map((conference, index) => (
                        <option key={index} value={conference}>{conference}</option>
                    ))}
                </select>
            </div>

            <div className="team-table">
                <div className="table-header">
                    <span onClick={() => handleSort("overall_rank")}>Overall Rank {sortColumn === "overall_rank" ? (sortOrder === "asc" ? "↑" : "↓") : ""}</span>
                    <span onClick={() => handleSort("team_name")}>Team Name {sortColumn === "team_name" ? (sortOrder === "asc" ? "↑" : "↓") : ""}</span>
                    <span onClick={() => handleSort("power_ranking")}>Power Ranking {sortColumn === "power_ranking" ? (sortOrder === "asc" ? "↑" : "↓") : ""}</span>
                    <span onClick={() => handleSort("division_rank")}>Rank - Division {sortColumn === "division_rank" ? (sortOrder === "asc" ? "↑" : "↓") : ""}</span>
                    <span onClick={() => handleSort("conference")}>Conference {sortColumn === "conference" ? (sortOrder === "asc" ? "↑" : "↓") : ""}</span>
                    <span onClick={() => handleSort("wins")}>Win - Loss {sortColumn === "wins" ? (sortOrder === "asc" ? "↑" : "↓") : ""}</span>
                </div>
                {currentTeams.map(team => (
                    <Link
                        to={`/user/${sportType}/${team.team_name}`}
                        key={team.team_id}
                        className="team-row"
                    >
                        <span>{team.overall_rank ?? 'N/A'}</span>
                        <span>{team.team_name}</span>
                        <span>{team.power_ranking?.[0] != null ? Number(team.power_ranking[0]).toFixed(2) : 'N/A'}</span>
                        <span>
                            {team.division_rank ?? 'N/A'} -
                            <span
                                onClick={(e) => { e.preventDefault(); }}
                                className="division-link"
                            >
                                {team.division ?? 'N/A'}
                            </span>
                        </span>
                        <span>{team.conference ?? 'N/A'}</span>
                        <span>{team.wins} - {team.losses}</span>
                    </Link>
                ))}
            </div>

            <div className="pagination">
                <button onClick={() => handlePageChange(currentPage - 1)} disabled={currentPage === 1}>
                    Previous
                </button>
                {Array.from({ length: totalPages }, (_, index) => (
                    <button
                        key={index}
                        onClick={() => handlePageChange(index + 1)}
                        className={currentPage === index + 1 ? 'active' : ''}
                    >
                        {index + 1}
                    </button>
                ))}
                <button
                    onClick={() => handlePageChange(currentPage + 1)}
                    disabled={currentPage === totalPages}
                >
                    Next
                </button>
            </div>
        </div>
    );
};

export default TeamsPage;
