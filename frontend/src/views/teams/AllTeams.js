import React, { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  CAlert,
  CFormInput,
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

const AllTeams = () => {
  const { sport: selectedSport, gender: selectedGender } = useParams()
  const [teams, setTeams] = useState([])
  const [failedDatasetCount, setFailedDatasetCount] = useState(0)
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const selectedDatasets = useMemo(
    () =>
      TEAM_DATASETS.filter(
        ({ sport, gender }) =>
          (!selectedSport || sport === selectedSport) &&
          (!selectedGender || gender === selectedGender),
      ),
    [selectedGender, selectedSport],
  )

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
    if (!normalizedSearch) return teams

    return teams.filter((team) =>
      [team.team_name, team.sport, team.gender, team.level]
        .map(formatDisplayName)
        .some((value) => value.toLowerCase().includes(normalizedSearch)),
    )
  }, [searchTerm, teams])

  const hasLoadFailures = failedDatasetCount > 0
  const directoryUnavailable = hasLoadFailures && teams.length === 0

  return (
    <div>
      <div className="d-flex flex-column flex-md-row align-items-md-center justify-content-between gap-3 mb-3">
        <h2 className="mb-0">{pageTitle}</h2>
        {!loading && teams.length > 0 && (
          <CFormInput
            aria-label="Search all teams"
            className="w-auto"
            onChange={(event) => setSearchTerm(event.target.value)}
            placeholder="Search teams..."
            type="search"
            value={searchTerm}
          />
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
          <CTable align="middle" hover responsive>
            <CTableHead color="light">
              <CTableRow>
                <CTableHeaderCell>Team</CTableHeaderCell>
                <CTableHeaderCell>Sport</CTableHeaderCell>
                <CTableHeaderCell>Gender</CTableHeaderCell>
                <CTableHeaderCell>Level</CTableHeaderCell>
                <CTableHeaderCell>Rank</CTableHeaderCell>
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
                  <CTableDataCell>{formatDisplayName(team.sport)}</CTableDataCell>
                  <CTableDataCell>{formatDisplayName(team.gender)}</CTableDataCell>
                  <CTableDataCell>{formatDisplayName(team.level)}</CTableDataCell>
                  <CTableDataCell>{team.overall_rank ?? '-'}</CTableDataCell>
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
