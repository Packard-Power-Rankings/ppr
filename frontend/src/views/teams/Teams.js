import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import api from "src/api";
import {
    CTable,
    CTableHead,
    CTableRow,
    CTableHeaderCell,
    CTableDataCell,
    CTableBody,
    CSpinner,
    CFormInput
} from '@coreui/react';

const Teams = () => {
    const { sport, gender, level } = useParams();
    const [teams, setTeams] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [searchTerm, setSearchTerm] = useState("");
    const [sortColumn, setSortColumn] = useState(null);
    const [sortDirection, setSortDirection] = useState("asc");

    const getLatestPowerRanking = (powerRanking) => {
        if (!powerRanking || powerRanking.length === 0) return '-';
        const rankingObj = powerRanking[0];
        const dates = Object.keys(rankingObj);
        const latestDate = dates[0];
        return parseFloat(rankingObj[latestDate]).toFixed(2);
    };

    const fetchTeams = async () => {
        try {
            setLoading(true);
            const teamsData = await api.get(
                `/teams/?sport_type=${sport}&gender=${gender}&level=${level}`
            );
            setTeams(teamsData.data.data.teams);
            setError(null);
        } catch (error) {
            console.log("Error fetching teams data", error);
            setError("Failed To Get Teams Data");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchTeams();
    }, [sport, gender, level]);

    const handleSearch = (event) => {
        setSearchTerm(event.target.value);
    };

    const handleSort = (column) => {
        if (sortColumn === column) {
            setSortDirection(sortDirection === "asc" ? "desc" : "asc");
        } else {
            setSortColumn(column);
            setSortDirection("asc");
        }
    };

    const filteredTeams = teams.filter(team =>
        team.team_name.toLowerCase().includes(searchTerm.toLowerCase())
    );

    const sortedTeams = [...filteredTeams].sort((a, b) => {
        if (!sortColumn) return 0;

        let valA = a[sortColumn];
        let valB = b[sortColumn];

        if (sortColumn === "power") {
            valA = parseFloat(getLatestPowerRanking(a.power_ranking)) || 0;
            valB = parseFloat(getLatestPowerRanking(b.power_ranking)) || 0;
        }

        if (valA < valB) return sortDirection === "asc" ? -1 : 1;
        if (valA > valB) return sortDirection === "asc" ? 1 : -1;
        return 0;
    });

    if (loading) {
        return (
            <div className="d-flex justify-content-center p-4">
                <CSpinner />
            </div>
        );
    }

    if (error) {
        return <div className="text-danger p-3">{error}</div>;
    }

    return (
        <div>
            <CFormInput
                type="text"
                placeholder="Search teams..."
                value={searchTerm}
                onChange={handleSearch}
                className="mb-3"
            />
            <CTable>
                <CTableHead color="light" style={{ position: 'sticky', top: 114, zIndex: 1 }}>
                    <CTableRow>
                        <CTableHeaderCell scope="col" className="py-3">Id</CTableHeaderCell>
                        <CTableHeaderCell scope="col" className="py-3" onClick={() => handleSort("overall_rank")} style={{ cursor: "pointer" }}>
                            Rank {sortColumn === "overall_rank" ? (sortDirection === "asc" ? "↑" : "↓") : ""}
                        </CTableHeaderCell>
                        <CTableHeaderCell scope="col" className="py-3">Team</CTableHeaderCell>
                        <CTableHeaderCell scope="col" className="py-3" onClick={() => handleSort("power")} style={{ cursor: "pointer" }}>
                            Power {sortColumn === "power" ? (sortDirection === "asc" ? "↑" : "↓") : ""}
                        </CTableHeaderCell>
                        <CTableHeaderCell scope="col" className="py-3" onClick={() => handleSort("division_rank")} style={{ cursor: "pointer" }}>
                            Div. Rank {sortColumn === "division_rank" ? (sortDirection === "asc" ? "↑" : "↓") : ""}
                        </CTableHeaderCell>
                        <CTableHeaderCell scope="col" className="py-3">Div.</CTableHeaderCell>
                        <CTableHeaderCell scope="col" className="py-3" onClick={() => handleSort("wins")} style={{ cursor: "pointer" }}>
                            W {sortColumn === "wins" ? (sortDirection === "asc" ? "↑" : "↓") : ""}
                        </CTableHeaderCell>
                        <CTableHeaderCell scope="col" className="py-3" onClick={() => handleSort("losses")} style={{ cursor: "pointer" }}>
                            L {sortColumn === "losses" ? (sortDirection === "asc" ? "↑" : "↓") : ""}
                        </CTableHeaderCell>
                    </CTableRow>
                </CTableHead>
                <CTableBody>
                    {sortedTeams.map((team) => (
                        <CTableRow key={team.id}>
                            <CTableDataCell className="py-3">{team.id}</CTableDataCell>
                            <CTableDataCell className="py-3">{team.overall_rank}</CTableDataCell>
                            <CTableDataCell className="py-3">
                                <Link to={`/team/${encodeURIComponent(team.team_name)}/${sport}/${gender}/${level}`}>
                                    {team.team_name}
                                </Link>
                            </CTableDataCell>
                            <CTableDataCell className="py-3">{getLatestPowerRanking(team.power_ranking)}</CTableDataCell>
                            <CTableDataCell className="py-3">{team.division_rank}</CTableDataCell>
                            <CTableDataCell className="py-3">{team.division}</CTableDataCell>
                            <CTableDataCell className="py-3">{team.wins}</CTableDataCell>
                            <CTableDataCell className="py-3">{team.losses}</CTableDataCell>
                        </CTableRow>
                    ))}
                </CTableBody>
            </CTable>
        </div>
    );
};

export default Teams;
