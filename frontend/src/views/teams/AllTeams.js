import React, { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  CAlert,
  CFormInput,
  CFormSelect,
  CSpinner,
  CTable,
  CTableBody,
  CTableDataCell,
  CTableHead,
  CTableHeaderCell,
  CTableRow,
} from '@coreui/react'
import api from 'src/api'
import { formatDisplayName } from 'src/utils/displayNames'

const TEAM_DATASETS = [
  { sport: 'football', gender: 'mens', level: 'high_school' },
  { sport: 'football', gender: 'mens', level: 'college' },
  { sport: 'basketball', gender: 'mens', level: 'high_school' },
  { sport: 'basketball', gender: 'mens', level: 'college' },
  { sport: 'basketball', gender: 'womens', level: 'high_school' },
  { sport: 'basketball', gender: 'womens', level: 'college' },
]

const getLatestPowerRanking = (powerRanking) => {
  if (!powerRanking || powerRanking.length === 0) return '-'
  const ranking = powerRanking[0]
  const latestDate = Object.keys(ranking)[0]
  const value = Number(ranking[latestDate])
  return Number.isFinite(value) ? value.toFixed(2) : '-'
}

const AllTeams = ({ fixedSport }) => {
  const { sport: routeSport, gender: selectedGender } = useParams()
  const selectedSport = fixedSport ?? routeSport
  const showSportColumn = !selectedSport
  const showGenderColumn = !selectedGender
  const [teams, setTeams] = useState([])
  const [failedDatasetCount, setFailedDatasetCount] = useState(0)
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [sportFilter, setSportFilter] = useState('all')
  const [genderFilter, setGenderFilter] = useState('all')
  const [levelFilter, setLevelFilter] = useState('all')
  const selectedDatasets = useMemo(
    () =>
      TEAM_DATASETS.filter(
        ({ sport, gender }) =>
          (!selectedSport || sport === selectedSport) &&
          (!selectedGender || gender === selectedGender),
      ),
    [selectedGender, selectedSport],
  )
  const sportOptions = [...new Set(selectedDatasets.map(({ sport }) => sport))]
  const genderOptions = [...new Set(selectedDatasets.map(({ gender }) => gender))]
  const levelOptions = [...new Set(selectedDatasets.map(({ level }) => level))]

  useEffect(() => {
    setSportFilter('all')
    setGenderFilter('all')
    setLevelFilter('all')
  }, [selectedGender, selectedSport])

  const pageTitle = selectedGender
    ? `${formatDisplayName(selectedGender)} ${formatDisplayName(selectedSport)} Teams`
    : selectedSport
      ? `${formatDisplayName(selectedSport)} Teams`
      : 'Teams'

  useEffect(() => {
    let isCurrentRequest = true

    const fetchAllTeams = async () => {
      setLoading(true)
      setFailedDatasetCount(0)

      const requests = selectedDatasets.map(async (dataset) => {
        const response = await api.get('/teams/', {
          params: {
            sport_type: dataset.sport,
            gender: dataset.gender,
            level: dataset.level,
          },
        })

        if (response.status === 204 || response.data?.status === 204) {
          return []
        }

        const datasetTeams = response.data?.data?.teams
        if (
          !Array.isArray(datasetTeams) ||
          datasetTeams.some((team) => typeof team?.team_name !== 'string')
        ) {
          throw new Error('Teams response did not contain a valid teams array')
        }

        return datasetTeams.map((team) => ({ ...team, ...dataset }))
      })

      const results = await Promise.allSettled(requests)
      if (!isCurrentRequest) return

      const loadedTeams = results
        .filter((result) => result.status === 'fulfilled')
        .flatMap((result) => result.value)
        .sort((teamA, teamB) => teamA.team_name.localeCompare(teamB.team_name))

      setTeams(loadedTeams)
      setFailedDatasetCount(results.filter((result) => result.status === 'rejected').length)
      setLoading(false)
    }

    fetchAllTeams()

    return () => {
      isCurrentRequest = false
    }
  }, [selectedDatasets])

  const filteredTeams = useMemo(() => {
    const normalizedSearch = searchTerm.trim().toLowerCase()
    return teams.filter((team) =>
      (sportFilter === 'all' || team.sport === sportFilter) &&
      (genderFilter === 'all' || team.gender === genderFilter) &&
      (levelFilter === 'all' || team.level === levelFilter) &&
      (!normalizedSearch || [team.team_name, team.sport, team.gender, team.level]
        .map(formatDisplayName)
        .some((value) => value.toLowerCase().includes(normalizedSearch))),
    )
  }, [genderFilter, levelFilter, searchTerm, sportFilter, teams])

  const hasLoadFailures = failedDatasetCount > 0
  const directoryUnavailable = hasLoadFailures && teams.length === 0

  return (
    <div>
      <div className="d-flex flex-column flex-md-row align-items-md-center justify-content-between gap-3 mb-3">
        <h2 className="mb-0">{pageTitle}</h2>
        {!loading && teams.length > 0 && (
          <div className="d-flex flex-wrap gap-2">
            {sportOptions.length > 1 && (
              <CFormSelect
                aria-label="Filter by Sport"
                className="w-auto"
                onChange={(event) => setSportFilter(event.target.value)}
                value={sportFilter}
              >
                <option value="all">All Sports</option>
                {sportOptions.map((sportOption) => (
                  <option key={sportOption} value={sportOption}>
                    {formatDisplayName(sportOption)}
                  </option>
                ))}
              </CFormSelect>
            )}
            {genderOptions.length > 1 && (
              <CFormSelect
                aria-label="Filter by Gender"
                className="w-auto"
                onChange={(event) => setGenderFilter(event.target.value)}
                value={genderFilter}
              >
                <option value="all">All Genders</option>
                {genderOptions.map((genderOption) => (
                  <option key={genderOption} value={genderOption}>
                    {formatDisplayName(genderOption)}
                  </option>
                ))}
              </CFormSelect>
            )}
            {levelOptions.length > 1 && (
              <CFormSelect
                aria-label="Filter by Level"
                className="w-auto"
                onChange={(event) => setLevelFilter(event.target.value)}
                value={levelFilter}
              >
                <option value="all">All Levels</option>
                {levelOptions.map((levelOption) => (
                  <option key={levelOption} value={levelOption}>
                    {formatDisplayName(levelOption)}
                  </option>
                ))}
              </CFormSelect>
            )}
            <CFormInput
              aria-label="Search all teams"
              className="w-auto"
              onChange={(event) => setSearchTerm(event.target.value)}
              placeholder="Search teams..."
              type="search"
              value={searchTerm}
            />
          </div>
        )}
      </div>

      {loading && (
        <div className="d-flex justify-content-center p-4">
          <CSpinner />
        </div>
      )}

      {!loading && directoryUnavailable && (
        <div className="text-danger p-3" role="alert">
          Failed to Load Teams Data
        </div>
      )}

      {!loading && !hasLoadFailures && teams.length === 0 && (
        <div className="text-primary p-3" role="status">
          No Team Data Found in Database
        </div>
      )}

      {!loading && teams.length > 0 && (
        <>
          {hasLoadFailures && (
            <CAlert color="danger">Some Teams Data Failed to Load</CAlert>
          )}
          <CTable align="middle" hover striped responsive className="team-list-table">
            <CTableHead color="light">
              <CTableRow>
                <CTableHeaderCell>Team</CTableHeaderCell>
                {showSportColumn && <CTableHeaderCell>Sport</CTableHeaderCell>}
                {showGenderColumn && <CTableHeaderCell>Gender</CTableHeaderCell>}
                <CTableHeaderCell>Level</CTableHeaderCell>
                <CTableHeaderCell>Rank</CTableHeaderCell>
                <CTableHeaderCell>Power</CTableHeaderCell>
                <CTableHeaderCell>Div Rank</CTableHeaderCell>
                <CTableHeaderCell><abbr title="Last Week Rank">LW Rank</abbr></CTableHeaderCell>
              </CTableRow>
            </CTableHead>
            <CTableBody>
              {filteredTeams.map((team) => (
                <CTableRow
                  key={`${team.sport}-${team.gender}-${team.level}-${team.id ?? team.team_name}`}
                >
                  <CTableDataCell>
                    <Link
                      to={`/team/${encodeURIComponent(team.team_name)}/${team.sport}/${team.gender}/${team.level}`}
                    >
                      {team.team_name}
                    </Link>
                  </CTableDataCell>
                  {showSportColumn && <CTableDataCell>{formatDisplayName(team.sport)}</CTableDataCell>}
                  {showGenderColumn && <CTableDataCell>{formatDisplayName(team.gender)}</CTableDataCell>}
                  <CTableDataCell>{formatDisplayName(team.level)}</CTableDataCell>
                  <CTableDataCell>{team.overall_rank ?? '-'}</CTableDataCell>
                  <CTableDataCell>{getLatestPowerRanking(team.power_ranking)}</CTableDataCell>
                  <CTableDataCell>{team.division_rank ?? '-'}</CTableDataCell>
                  <CTableDataCell>{team.last_rank ?? '-'}</CTableDataCell>
                </CTableRow>
              ))}
            </CTableBody>
          </CTable>
          {filteredTeams.length === 0 && (
            <div className="text-body-secondary p-3" role="status">
              No Teams Match Your Search
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default AllTeams
