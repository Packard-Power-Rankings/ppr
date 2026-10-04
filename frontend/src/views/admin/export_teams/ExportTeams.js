import React, { useState } from 'react'
import {
  CAlert,
  CButton,
  CSpinner,
} from '@coreui/react'
import { useSelector } from 'react-redux'
import api from 'src/api'

const TEAM_EXPORT_COLUMNS = [
  ['team_id', 'Team ID'],
  ['overall_rank', 'Current Rank'],
  ['last_rank', 'Last Rank'],
  ['short_name', 'Short Name'],
  ['long_name', 'Long Name'],
  ['state', 'State'],
  ['power_ranking', 'Power Rank'],
  ['division', 'Div'],
  ['division_rank', 'Div Rank'],
  ['conference', 'Conference'],
  ['conference_rank', 'Conf. Rank'],
  ['wins', 'Total Wins'],
  ['losses', 'Total Loss'],
  ['ties', 'Total Ties'],
  ['ranked', 'Ranked'],
]

const formatHeader = (key) => key.replace(/_/g, ' ').replace(/\b\w/g, (letter) => letter.toUpperCase())

const getLatestPowerRank = (powerRanking) => {
  if (!Array.isArray(powerRanking)) return powerRanking ?? ''
  for (let index = powerRanking.length - 1; index >= 0; index -= 1) {
    const entry = powerRanking[index]
    if (entry && typeof entry === 'object' && Object.keys(entry).length > 0) {
      return Object.values(entry)[0]
    }
  }
  return ''
}

const getExportValue = (team, key) => {
  if (key === 'short_name') {
    const names = [...new Set([team.team_name, team.short_name].filter(Boolean))]
    return names.length > 1 ? `${names[0]} (${names[1]})` : names[0] || ''
  }
  if (key === 'power_ranking') return getLatestPowerRank(team.power_ranking)
  return team[key]
}

const escapeCsvValue = (value) => {
  const text = value == null
    ? ''
    : typeof value === 'object'
      ? JSON.stringify(value)
      : String(value)
  return `"${text.replace(/"/g, '""')}"`
}

const getSortableRank = (rank) => {
  const numericRank = Number(rank)
  return Number.isFinite(numericRank) && numericRank > 0 ? numericRank : Infinity
}

const sortTeamsByRank = (teams) => [...teams].sort((teamA, teamB) =>
  getSortableRank(teamA.overall_rank) - getSortableRank(teamB.overall_rank) ||
  String(teamA.team_name ?? '').localeCompare(String(teamB.team_name ?? '')))

const createTeamsCsv = (teams) => {
  const availableKeys = new Set(teams.flatMap((team) => Object.keys(team)))
  const extraColumns = [...availableKeys]
    .filter((key) => !['date', 'team_name', 'season_opp'].includes(key) &&
      !TEAM_EXPORT_COLUMNS.some(([column]) => column === key))
    .sort()
    .map((key) => [key, key === 'recent_opp' ? 'Recent Opp IDs' : formatHeader(key)])
  const columns = [...TEAM_EXPORT_COLUMNS, ...extraColumns]
  return [
    columns.map(([, label]) => escapeCsvValue(label)).join(','),
    ...sortTeamsByRank(teams).map((team) => columns
      .map(([key]) => escapeCsvValue(getExportValue(team, key)))
      .join(',')),
  ].join('\r\n')
}

const ExportTeams = () => {
  const sport = useSelector((state) => state.sport)
  const gender = useSelector((state) => state.gender)
  const level = useSelector((state) => state.level)
  const [exporting, setExporting] = useState(false)
  const [feedback, setFeedback] = useState(null)

  const exportSelectedTeams = async () => {
    setExporting(true)
    setFeedback(null)
    try {
      const { data } = await api.get('/export_teams/', {
        params: { sport_type: sport, gender, level },
      })
      const teams = Array.isArray(data?.teams) ? data.teams : []
      const blob = new Blob([createTeamsCsv(teams)], { type: 'text/csv;charset=utf-8' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `${sport}_${gender}_${level}_teams.csv`
      document.body.appendChild(link)
      link.click()
      link.remove()
      URL.revokeObjectURL(url)
      setFeedback({
        color: 'success',
        message: `Exported ${teams.length} teams to CSV.`,
      })
    } catch (error) {
      setFeedback({
        color: 'danger',
        message: error.response?.data?.detail || 'Failed to export selected teams.',
      })
    } finally {
      setExporting(false)
    }
  }

  return (
    <div className="mb-4">
      <h1 className="h3 mb-4">Export Teams</h1>
      {feedback && <CAlert color={feedback.color} role="status">{feedback.message}</CAlert>}
      <div className="border rounded p-4">
        <CButton
          type="button"
          color="primary"
          onClick={exportSelectedTeams}
          disabled={exporting}
        >
          {exporting && <CSpinner size="sm" className="me-2" />}
          Selected Teams only as CSV
        </CButton>
      </div>
    </div>
  )
}

export default ExportTeams
