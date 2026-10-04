import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import api from "src/api";
import { formatDatasetName } from "src/utils/displayNames";
import {
    CTable,
    CTableHead,
    CTableRow,
    CTableHeaderCell,
    CTableDataCell,
    CTableBody,
    CSpinner,
    CFormInput,
    CFormSelect,
} from '@coreui/react';

const Teams = ({ fixedSport }) => {
    const { sport: routeSport, gender, level } = useParams();
    const sport = fixedSport ?? routeSport;
    const [teams, setTeams] = useState([]);
    const [requestStatus, setRequestStatus] = useState('loading');
    const [searchTerm, setSearchTerm] = useState("");
    const [divisionFilter, setDivisionFilter] = useState('all');
    const [conferenceFilter, setConferenceFilter] = useState('all');
    const [sortColumn, setSortColumn] = useState("overall_rank");
    const [sortDirection, setSortDirection] = useState("asc");
    const selectionName = formatDatasetName({ sport, gender, level });
    const pageHeading = (
        <h1 className="h2 mb-3">{selectionName} Ranking</h1>
    );

    const getLatestPowerRanking = (powerRanking) => {
        if (!powerRanking || powerRanking.length === 0) return '-';
        const rankingObj = powerRanking[0];
        const dates = Object.keys(rankingObj);
        const latestDate = dates[0];
        return parseFloat(rankingObj[latestDate]).toFixed(2);
    };

    const getDisplayRank = (rank) => {
        const numericRank = Number(rank);
        return Number.isFinite(numericRank) && numericRank > 0 ? numericRank : 9999;
    };

    const getRankMovement = (currentRank, lastRank) => {
        const current = Number(currentRank);
        const last = Number(lastRank);
        if (!Number.isFinite(current) || !Number.isFinite(last) || current <= 0 || last <= 0) {
            return null;
        }

        const change = last - current;
        const places = Math.abs(change);
        if (places < 2) return null;

        const arrowCount = places >= 10 ? 3 : places >= 5 ? 2 : 1;
        const direction = change > 0 ? 'up' : 'down';
        return {
            direction,
            places,
            arrow: (direction === 'up' ? '↑' : '↓').repeat(arrowCount),
        };
    };

    useEffect(() => {
        let isCurrentRequest = true;

        const fetchTeams = async () => {
            setRequestStatus('loading');
            setTeams([]);

            try {
                const { data: response } = await api.get('/teams/', {
                    params: {
                        sport_type: sport,
                        gender,
                        level,
                    },
                });

                if (!isCurrentRequest) return;

                if (response?.status === 204 && response?.data === null) {
                    setRequestStatus('empty');
                    return;
                }

                const loadedTeams = response?.data?.teams;
                if (!Array.isArray(loadedTeams)) {
                    throw new Error('Teams response did not contain a teams array');
                }

                setTeams(loadedTeams);
                setRequestStatus(loadedTeams.length === 0 ? 'empty' : 'success');
            } catch (error) {
                if (!isCurrentRequest) return;

                console.error("Error fetching teams data", error);
                setRequestStatus('error');
            }
        };

        fetchTeams();

        return () => {
            isCurrentRequest = false;
        };
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

    const getAriaSort = (column) => {
        if (sortColumn !== column) return undefined;
        return sortDirection === "asc" ? "ascending" : "descending";
    };

    const renderSortArrow = (column) => (
        sortColumn === column
            ? <span aria-hidden="true">{sortDirection === "asc" ? "↑" : "↓"}</span>
            : null
    );

    const filteredTeams = teams.filter(team =>
        team.team_name.toLowerCase().includes(searchTerm.toLowerCase()) &&
        (divisionFilter === 'all' || team.division === divisionFilter) &&
        (conferenceFilter === 'all' || team.conference === conferenceFilter)
    );

    const divisionOptions = [...new Set(teams.map((team) => team.division).filter(Boolean))]
        .sort((first, second) => first.localeCompare(second));
    const conferenceOptions = [...new Set(teams.map((team) => team.conference).filter(Boolean))]
        .sort((first, second) => first.localeCompare(second));
    const hasConference = teams.some((team) =>
        typeof team.conference === 'string' && team.conference.trim().length > 0
    );

    const sortedTeams = [...filteredTeams].sort((a, b) => {
        if (!sortColumn) return 0;

        let valA = a[sortColumn];
        let valB = b[sortColumn];

        if (sortColumn === "power") {
            valA = parseFloat(getLatestPowerRanking(a.power_ranking)) || 0;
            valB = parseFloat(getLatestPowerRanking(b.power_ranking)) || 0;
        } else if (["overall_rank", "last_rank", "conference_rank"].includes(sortColumn)) {
            valA = getDisplayRank(a[sortColumn]);
            valB = getDisplayRank(b[sortColumn]);
        }

        if (valA < valB) return sortDirection === "asc" ? -1 : 1;
        if (valA > valB) return sortDirection === "asc" ? 1 : -1;
        return 0;
    });

    if (requestStatus === 'loading') {
        return (
            <div>
                {pageHeading}
                <div className="d-flex justify-content-center p-4">
                    <CSpinner />
                </div>
            </div>
        );
    }

    if (requestStatus === 'empty') {
        return (
            <div>
                {pageHeading}
                <div className="text-primary p-3" role="status">
                    No Data Found in Database for {selectionName}
                </div>
            </div>
        );
    }

    if (requestStatus === 'error') {
        return (
            <div>
                {pageHeading}
                <div className="text-danger p-3" role="alert">
                    Failed to Load {selectionName} Data
                </div>
            </div>
        );
    }

    return (
        <div>
            {pageHeading}
            <div className="d-flex flex-column flex-md-row gap-2 mb-3">
                <CFormInput
                    type="text"
                    aria-label="Search teams"
                    placeholder="Search teams..."
                    value={searchTerm}
                    onChange={handleSearch}
                    className="flex-grow-1"
                />
                <CFormSelect
                    aria-label="Filter by Division"
                    className="w-auto"
                    value={divisionFilter}
                    onChange={(event) => setDivisionFilter(event.target.value)}
                >
                    <option value="all">All Divisions</option>
                    {divisionOptions.map((division) => (
                        <option key={division} value={division}>{division}</option>
                    ))}
                </CFormSelect>
                <CFormSelect
                    aria-label="Filter by Conference"
                    className="w-auto"
                    value={conferenceFilter}
                    onChange={(event) => setConferenceFilter(event.target.value)}
                >
                    <option value="all">All Conferences</option>
                    {conferenceOptions.map((conference) => (
                        <option key={conference} value={conference}>{conference}</option>
                    ))}
                </CFormSelect>
            </div>
            <CTable striped className="team-list-table">
                <CTableHead color="light" style={{ position: 'sticky', top: 114, zIndex: 1 }}>
                    <CTableRow>
                        <CTableHeaderCell scope="col" className="py-3" onClick={() => handleSort("overall_rank")} aria-sort={getAriaSort("overall_rank")} style={{ cursor: "pointer" }}>
                            Rank {renderSortArrow("overall_rank")}
                        </CTableHeaderCell>
                        <CTableHeaderCell scope="col" className="py-3" onClick={() => handleSort("last_rank")} aria-sort={getAriaSort("last_rank")} style={{ cursor: "pointer" }}>
                            <abbr title="Last Week Rank">LW Rank</abbr> {renderSortArrow("last_rank")}
                        </CTableHeaderCell>
                        <CTableHeaderCell scope="col" className="py-3">Team</CTableHeaderCell>
                        <CTableHeaderCell scope="col" className="py-3" onClick={() => handleSort("power")} aria-sort={getAriaSort("power")} style={{ cursor: "pointer" }}>
                            Power {renderSortArrow("power")}
                        </CTableHeaderCell>
                        <CTableHeaderCell scope="col" className="py-3" onClick={() => handleSort("division_rank")} aria-sort={getAriaSort("division_rank")} style={{ cursor: "pointer" }}>
                            Div. Rank {renderSortArrow("division_rank")}
                        </CTableHeaderCell>
                        <CTableHeaderCell scope="col" className="py-3">Div.</CTableHeaderCell>
                        {hasConference && (
                            <CTableHeaderCell scope="col" className="py-3">Conference</CTableHeaderCell>
                        )}
                        {hasConference && (
                            <CTableHeaderCell scope="col" className="py-3" onClick={() => handleSort("conference_rank")} aria-sort={getAriaSort("conference_rank")} style={{ cursor: "pointer" }}>
                                <abbr title="Conference Rank">Conf. Rank</abbr> {renderSortArrow("conference_rank")}
                            </CTableHeaderCell>
                        )}
                        <CTableHeaderCell scope="col" className="py-3" onClick={() => handleSort("wins")} aria-sort={getAriaSort("wins")} style={{ cursor: "pointer" }}>
                            W {renderSortArrow("wins")}
                        </CTableHeaderCell>
                        <CTableHeaderCell scope="col" className="py-3" onClick={() => handleSort("losses")} aria-sort={getAriaSort("losses")} style={{ cursor: "pointer" }}>
                            L {renderSortArrow("losses")}
                        </CTableHeaderCell>
                    </CTableRow>
                </CTableHead>
                <CTableBody>
                    {sortedTeams.map((team) => {
                        const movement = getRankMovement(team.overall_rank, team.last_rank);
                        return (
                            <CTableRow key={team.id}>
                            <CTableDataCell className="py-3">
                                {getDisplayRank(team.overall_rank)}
                                {movement && (
                                    <span
                                        className={`ms-2 ${movement.direction === 'up' ? 'text-success' : 'text-danger'}`}
                                        role="img"
                                        aria-label={`${movement.direction === 'up' ? 'Up' : 'Down'} ${movement.places} places`}
                                        title={`${movement.direction === 'up' ? 'Up' : 'Down'} ${movement.places} places`}
                                    >
                                        {movement.arrow}
                                    </span>
                                )}
                            </CTableDataCell>
                            <CTableDataCell className="py-3">{team.last_rank ?? '-'}</CTableDataCell>
                            <CTableDataCell className="py-3">
                                <Link to={`/team/${encodeURIComponent(team.team_name)}/${sport}/${gender}/${level}`}>
                                    {team.team_name}
                                </Link>
                            </CTableDataCell>
                            <CTableDataCell className="py-3">{getLatestPowerRanking(team.power_ranking)}</CTableDataCell>
                            <CTableDataCell className="py-3">{team.division_rank}</CTableDataCell>
                            <CTableDataCell className="py-3">{team.division}</CTableDataCell>
                            {hasConference && <CTableDataCell className="py-3">{team.conference}</CTableDataCell>}
                            {hasConference && (
                                <CTableDataCell className="py-3">
                                    {Number(team.conference_rank) > 0 ? team.conference_rank : '-'}
                                </CTableDataCell>
                            )}
                            <CTableDataCell className="py-3">{team.wins}</CTableDataCell>
                            <CTableDataCell className="py-3">{team.losses}</CTableDataCell>
                            </CTableRow>
                        );
                    })}
                </CTableBody>
            </CTable>
        </div>
    );
};

export default Teams;
