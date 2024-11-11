import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import './TeamsPage.css';

const TeamsPage = () => {
    const { sportType } = useParams();
    const [teams, setTeams] = useState([]);
    const [visibleTeams, setVisibleTeams] = useState([]);
    const [offset, setOffset] = useState(10);
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState("");
    const [sortColumn, setSortColumn] = useState(null);
    const [sortOrder, setSortOrder] = useState("asc");
    const [divisionFilter, setDivisionFilter] = useState(null); // New state to store division filter

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
                setVisibleTeams(data.data.teams.slice(0, offset));
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

    // Load more teams on scroll
    const loadMoreTeams = () => {
        const filteredTeams = applySortingAndFiltering();
        setVisibleTeams(filteredTeams.slice(0, visibleTeams.length + offset));
    };

    // Modified applySortingAndFiltering function to handle filtering for specific divisions
    const applySortingAndFiltering = () => {
        const filteredTeams = teams.filter((team) => {
            // Only filter by team name if there's a search query
            return team.team_name.toLowerCase().includes(searchQuery.toLowerCase());
        });

        // Sort based on selected column and order
        return filteredTeams.sort((a, b) => {
            if (!sortColumn) return 0;
            const valA = a[sortColumn];
            const valB = b[sortColumn];

            if (valA == null || valB == null) return 0; // Handle null values
            if (sortOrder === "asc") return valA > valB ? 1 : -1;
            else return valA < valB ? 1 : -1;
        });
    };

    // Handle search input changes
    const handleSearchChange = (e) => {
        setSearchQuery(e.target.value);
        const filteredTeams = applySortingAndFiltering();
        setVisibleTeams(filteredTeams.slice(0, offset));
    };

    // Handle sorting when column headers are clicked
    const handleSort = (column) => {
        const order = (sortColumn === column && sortOrder === "asc") ? "desc" : "asc";
        setSortColumn(column);
        setSortOrder(order);
        const sortedTeams = applySortingAndFiltering();
        setVisibleTeams(sortedTeams.slice(0, offset));
    };

    // Add this function within your TeamsPage component
    const handleDivisionClick = (division) => {
        // Filter teams by the selected division
        const filteredTeams = teams.filter((team) => team.division === division);
        
        // Update the visibleTeams to display only teams in the selected division
        setVisibleTeams(filteredTeams);
        setSortColumn(null); // Reset any sorting
        setSearchQuery("");   // Clear search query if needed
    };

    // Clear the division filter
    const clearDivisionFilter = () => {
        setDivisionFilter(null);
        const filteredTeams = applySortingAndFiltering();
        setVisibleTeams(filteredTeams.slice(0, offset));
    };

    // Scroll event listener for infinite scroll
    const handleScroll = () => {
        if (window.innerHeight + document.documentElement.scrollTop >= document.documentElement.offsetHeight - 50) {
            loadMoreTeams();
        }
    };

    useEffect(() => {
        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, [visibleTeams, teams, searchQuery, sortColumn, sortOrder, divisionFilter]);

    if (loading) return <p>Loading...</p>;
    if (error) return <p>Error: {error}</p>;

    return (
        <div>
            <h2>{sportType.charAt(0).toUpperCase() + sportType.slice(1)} Teams</h2>

            {/* Search input field */}
            <input
                type="text"
                placeholder="Search teams..."
                value={searchQuery}
                onChange={handleSearchChange}
                className="search-input"
            />

            {/* Clear Division Filter Button */}
            {divisionFilter && (
                <button onClick={clearDivisionFilter} className="clear-filter">
                    Clear Division Filter ({divisionFilter})
                </button>
            )}

            <div className="team-table">
                <div className="table-header">
                    <span onClick={() => handleSort("overall_rank")}>Overall Rank {sortColumn === "overall_rank" ? (sortOrder === "asc" ? "↑" : "↓") : ""}</span>
                    <span onClick={() => handleSort("team_name")}>Team Name {sortColumn === "team_name" ? (sortOrder === "asc" ? "↑" : "↓") : ""}</span>
                    <span onClick={() => handleSort("power_ranking")}>Power Ranking {sortColumn === "power_ranking" ? (sortOrder === "asc" ? "↑" : "↓") : ""}</span>
                    <span onClick={() => handleSort("division_rank")}>Rank - Division {sortColumn === "division_rank" ? (sortOrder === "asc" ? "↑" : "↓") : ""}</span>
                    <span onClick={() => handleSort("conference")}>Conference {sortColumn === "conference" ? (sortOrder === "asc" ? "↑" : "↓") : ""}</span>
                    <span onClick={() => handleSort("wins")}>Win - Loss {sortColumn === "wins" ? (sortOrder === "asc" ? "↑" : "↓") : ""}</span>
                </div>
                {visibleTeams.map(team => (
                    <Link
                        to={`/user/${sportType}/${team.team_name}`}
                        key={team.team_id}
                        className="team-row"
                    >
                        <span>{team.overall_rank ?? 'N/A'}</span>
                        <span>{team.team_name}</span>
                        <span>{team.power_ranking?.[0]?.toFixed(2) ?? 'N/A'}</span>
                        {/* Combined Division Rank and Division with clickable division */}
                        <span>
                            {team.division_rank ?? 'N/A'} - 
                            <span 
                                onClick={(e) => { e.preventDefault(); handleDivisionClick(team.division); }}
                                style={{ cursor: 'pointer', color: 'blue', marginLeft: '5px' }}
                            >
                                {team.division ?? 'N/A'}
                            </span>
                        </span>
                        <span>{team.conference ?? 'N/A'}</span>
                        <span>{team.wins} - {team.losses}</span>
                    </Link>
                ))}
            </div>
        </div>
    );
};

export default TeamsPage;
