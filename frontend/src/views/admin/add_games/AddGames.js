import React, { useEffect, useMemo, useState } from 'react'
import { useSelector } from 'react-redux'
import {
  CAlert,
  CButton,
  CButtonGroup,
  CCol,
  CForm,
  CFormInput,
  CFormLabel,
  CFormSelect,
  CModal,
  CModalBody,
  CModalFooter,
  CModalHeader,
  CModalTitle,
  CRow,
  CSpinner,
  CTable,
  CTableBody,
  CTableDataCell,
  CTableHead,
  CTableHeaderCell,
  CTableRow,
} from '@coreui/react'
import CIcon from '@coreui/icons-react'
import { cilInfo } from '@coreui/icons'
import Papa from 'papaparse'
import Select from 'react-select'
import api from 'src/api'
import { formatDisplayName } from 'src/utils/displayNames'
import { apiErrorMessages, GAME_COLUMNS, validateGameRows } from './gameFileValidation'

const emptyGame = {
  date: '',
  home_team: '',
  away_team: '',
  home_score: '',
  away_score: '',
  neutral_site: '0',
}

const AddGames = () => {
  const sport = useSelector((state) => state.sport)
  const gender = useSelector((state) => state.gender)
  const level = useSelector((state) => state.level)
  const [mode, setMode] = useState('upload')
  const [pendingFile, setPendingFile] = useState(null)
  const [fileName, setFileName] = useState('')
  const [games, setGames] = useState([])
  const [validationErrors, setValidationErrors] = useState([])
  const [confirmedDataset, setConfirmedDataset] = useState(null)
  const [confirmationVisible, setConfirmationVisible] = useState(false)
  const [helpVisible, setHelpVisible] = useState(false)
  const [feedback, setFeedback] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [fileInputKey, setFileInputKey] = useState(0)
  const [manualGame, setManualGame] = useState(emptyGame)
  const [teamOptions, setTeamOptions] = useState([])
  const [loadingTeams, setLoadingTeams] = useState(false)
  const [teamLoadError, setTeamLoadError] = useState(false)

  const datasetKey = `${sport}:${gender}:${level}`
  const datasetName = useMemo(() => [gender, level, sport]
    .map(formatDisplayName)
    .join(' '), [gender, level, sport])
  const query = `sport_type=${sport}&gender=${gender}&level=${level}`

  useEffect(() => {
    if (mode !== 'manual') return undefined

    let isCurrentRequest = true
    const fetchTeams = async () => {
      setLoadingTeams(true)
      setTeamLoadError(false)
      setTeamOptions([])
      setManualGame(emptyGame)

      try {
        const response = await api.get('/teams-ids/', {
          params: { sport_type: sport, gender, level },
        })
        if (!isCurrentRequest) return

        const teams = response.status === 204 || response.data?.status === 204
          ? []
          : response.data?.data?.teams
        if (!Array.isArray(teams)) {
          throw new Error('Teams response did not contain a teams array')
        }
        setTeamOptions(teams.map((team) => ({
          value: team.team_id,
          label: team.team_name,
        })))
      } catch (error) {
        if (!isCurrentRequest) return
        console.error('Failed to load teams for manual game entry', error)
        setTeamLoadError(true)
      } finally {
        if (isCurrentRequest) setLoadingTeams(false)
      }
    }

    fetchTeams()
    return () => {
      isCurrentRequest = false
    }
  }, [gender, level, mode, sport])

  const clearUpload = () => {
    setPendingFile(null)
    setFileName('')
    setGames([])
    setValidationErrors([])
    setConfirmedDataset(null)
    setFileInputKey((value) => value + 1)
  }

  useEffect(() => {
    if (confirmedDataset && confirmedDataset !== datasetKey) {
      clearUpload()
      setFeedback({
        color: 'warning',
        messages: ['The selected dataset changed. Choose the game file again to confirm its destination.'],
      })
    }
  }, [datasetKey, confirmedDataset])

  const handleFileSelection = (event) => {
    const file = event.target.files?.[0]
    setFeedback(null)
    setValidationErrors([])
    setGames([])
    setConfirmedDataset(null)
    if (!file) return
    setPendingFile(file)
    setFileName(file.name)
    setConfirmationVisible(true)
  }

  const parseConfirmedFile = () => {
    setConfirmationVisible(false)
    if (!pendingFile) return

    Papa.parse(pendingFile, {
      skipEmptyLines: 'greedy',
      complete: (result) => {
        const parserErrors = result.errors.map(
          (error) => `Row ${(error.row ?? 0) + 1}: ${error.message}.`,
        )
        const validation = validateGameRows(result.data)
        const errors = [...parserErrors, ...validation.errors]
        setValidationErrors(errors)
        setGames(errors.length ? [] : validation.games)
        setConfirmedDataset(datasetKey)
      },
      error: (error) => {
        setValidationErrors([`Unable to read the game file: ${error.message}`])
        setConfirmedDataset(datasetKey)
      },
    })
  }

  const cancelFileConfirmation = () => {
    setConfirmationVisible(false)
    clearUpload()
  }

  const submitUpload = async () => {
    const validation = validateGameRows(games)
    if (validation.errors.length) {
      setValidationErrors(validation.errors)
      return
    }
    if (confirmedDataset !== datasetKey) {
      setValidationErrors(['Choose and confirm the game file for the currently selected dataset.'])
      return
    }

    const csv = Papa.unparse(validation.games, { header: false, newline: '\n' })
    const formData = new FormData()
    formData.append('csv_file', new File([csv], fileName, { type: 'text/csv' }))
    setSubmitting(true)
    setFeedback(null)
    try {
      const { data } = await api.post(`/games/upload/?${query}`, formData)
      setFeedback({ color: 'success', messages: [data.message] })
      clearUpload()
    } catch (error) {
      setFeedback({
        color: 'danger',
        messages: apiErrorMessages(error, 'Failed to upload the game file.'),
      })
    } finally {
      setSubmitting(false)
    }
  }

  const updateManualGame = (field, value) => {
    setManualGame((current) => ({ ...current, [field]: value }))
  }

  const submitManualGame = async (event) => {
    event.preventDefault()
    const row = GAME_COLUMNS.map((column) => manualGame[column])
    const validation = validateGameRows([row])
    if (validation.errors.length) {
      setFeedback({ color: 'danger', messages: validation.errors })
      return
    }

    const [validated] = validation.games
    const payload = Object.fromEntries(GAME_COLUMNS.map((column, index) => [
      column,
      ['home_score', 'away_score', 'neutral_site'].includes(column)
        ? Number(validated[index])
        : validated[index],
    ]))
    setSubmitting(true)
    setFeedback(null)
    try {
      const { data } = await api.post(`/games/?${query}`, payload)
      setFeedback({ color: 'success', messages: [data.message] })
      setManualGame(emptyGame)
    } catch (error) {
      setFeedback({
        color: 'danger',
        messages: apiErrorMessages(error, 'Failed to add the game.'),
      })
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="mb-4">
      <h1 className="h3 mb-3">Add Games</h1>
      <CButtonGroup role="group" aria-label="Add games method" className="mb-4">
        <CButton
          color="primary"
          variant={mode === 'upload' ? undefined : 'outline'}
          onClick={() => setMode('upload')}
        >
          Upload Game File
        </CButton>
        <CButton
          color="primary"
          variant={mode === 'manual' ? undefined : 'outline'}
          onClick={() => setMode('manual')}
        >
          Add One Game
        </CButton>
      </CButtonGroup>

      {feedback && (
        <CAlert color={feedback.color} dismissible onClose={() => setFeedback(null)}>
          {feedback.messages.map((message) => <div key={message}>{message}</div>)}
        </CAlert>
      )}

      {mode === 'upload' ? (
        <>
          <div className="p-4 border rounded mb-4">
            <div className="d-flex align-items-center justify-content-between gap-3 mb-3">
              <h2 className="h5 mb-0">Upload Game File For {datasetName}</h2>
              <CButton
                color="secondary"
                variant="ghost"
                size="sm"
                aria-label="Show game file format"
                title="Show game file format"
                onClick={() => setHelpVisible(true)}
              >
                <CIcon icon={cilInfo} />
              </CButton>
            </div>
            <CFormInput
              key={fileInputKey}
              type="file"
              accept=".csv,text/csv"
              id="game-file"
              label="Choose CSV game file"
              onChange={handleFileSelection}
              disabled={submitting}
            />
            {validationErrors.length > 0 && (
              <CAlert color="danger" className="mt-3 mb-0">
                {validationErrors.map((message) => <div key={message}>{message}</div>)}
              </CAlert>
            )}
            <CButton
              color="primary"
              className="mt-3"
              onClick={submitUpload}
              disabled={!games.length || submitting}
            >
              {submitting && <CSpinner size="sm" className="me-2" />}
              Submit Game File
            </CButton>
          </div>

          {games.length > 0 && (
            <div className="table-responsive">
              <CTable striped hover>
                <CTableHead>
                  <CTableRow>
                    {GAME_COLUMNS.map((column) => (
                      <CTableHeaderCell key={column}>{formatDisplayName(column)}</CTableHeaderCell>
                    ))}
                  </CTableRow>
                </CTableHead>
                <CTableBody>
                  {games.map((row, rowIndex) => (
                    <CTableRow key={`${row[0]}-${row[1]}-${row[2]}-${rowIndex}`}>
                      {row.map((cell, columnIndex) => (
                        <CTableDataCell key={GAME_COLUMNS[columnIndex]}>{cell}</CTableDataCell>
                      ))}
                    </CTableRow>
                  ))}
                </CTableBody>
              </CTable>
            </div>
          )}
        </>
      ) : (
        <>
          {teamLoadError && (
            <CAlert color="danger">Failed to load teams for {datasetName}.</CAlert>
          )}
          {!loadingTeams && !teamLoadError && teamOptions.length === 0 && (
            <CAlert color="info">No teams found for {datasetName}.</CAlert>
          )}
          <CForm className="p-4 border rounded" onSubmit={submitManualGame}>
            <h2 className="h5 mb-3">Add One Game For {datasetName}</h2>
            <CRow className="g-3">
              <CCol md={4}>
                <CFormInput
                  type="date"
                  id="game-date"
                  label="Game Date"
                  value={manualGame.date}
                  onChange={(event) => updateManualGame('date', event.target.value)}
                  required
                />
              </CCol>
              <CCol md={4}>
                <CFormLabel htmlFor="home-team">Home Team</CFormLabel>
                <Select
                  aria-label="Home Team"
                  classNamePrefix="react-select"
                  inputId="home-team"
                  isDisabled={loadingTeams || teamLoadError || !teamOptions.length}
                  isLoading={loadingTeams}
                  isSearchable
                  onChange={(option) => {
                    const homeTeam = option?.label || ''
                    setManualGame((current) => ({
                      ...current,
                      home_team: homeTeam,
                      away_team: current.away_team === homeTeam ? '' : current.away_team,
                    }))
                  }}
                  options={teamOptions.filter((team) => team.label !== manualGame.away_team)}
                  placeholder="Search and select a team"
                  required
                  value={teamOptions.find((team) => team.label === manualGame.home_team) || null}
                />
              </CCol>
              <CCol md={4}>
                <CFormLabel htmlFor="away-team">Away Team</CFormLabel>
                <Select
                  aria-label="Away Team"
                  classNamePrefix="react-select"
                  inputId="away-team"
                  isDisabled={loadingTeams || teamLoadError || !teamOptions.length}
                  isLoading={loadingTeams}
                  isSearchable
                  onChange={(option) => updateManualGame('away_team', option?.label || '')}
                  options={teamOptions.filter((team) => team.label !== manualGame.home_team)}
                  placeholder="Search and select a team"
                  required
                  value={teamOptions.find((team) => team.label === manualGame.away_team) || null}
                />
              </CCol>
              <CCol md={4}>
                <CFormInput
                  type="number"
                  min="0"
                  step="1"
                  id="home-score"
                  label="Home Score"
                  value={manualGame.home_score}
                  onChange={(event) => updateManualGame('home_score', event.target.value)}
                  required
                />
              </CCol>
              <CCol md={4}>
                <CFormInput
                  type="number"
                  min="0"
                  step="1"
                  id="away-score"
                  label="Away Score"
                  value={manualGame.away_score}
                  onChange={(event) => updateManualGame('away_score', event.target.value)}
                  required
                />
              </CCol>
              <CCol md={4}>
                <CFormLabel htmlFor="neutral-site">Location</CFormLabel>
                <CFormSelect
                  id="neutral-site"
                  value={manualGame.neutral_site}
                  onChange={(event) => updateManualGame('neutral_site', event.target.value)}
                >
                  <option value="0">Home field</option>
                  <option value="999">Neutral site</option>
                </CFormSelect>
              </CCol>
            </CRow>
            <CButton
              type="submit"
              color="primary"
              className="mt-3"
              disabled={submitting || loadingTeams || teamLoadError || !teamOptions.length}
            >
              {submitting && <CSpinner size="sm" className="me-2" />}
              Add Game
            </CButton>
          </CForm>
        </>
      )}

      <CModal
        visible={confirmationVisible}
        onClose={() => setConfirmationVisible(false)}
        backdrop="static"
      >
        <CModalHeader>
          <CModalTitle>Confirm Game File</CModalTitle>
        </CModalHeader>
        <CModalBody>
          Is <strong>{fileName}</strong> a game file for <strong>{datasetName}</strong>?
          The file will not be parsed until you confirm.
        </CModalBody>
        <CModalFooter>
          <CButton color="secondary" variant="outline" onClick={cancelFileConfirmation}>
            Cancel
          </CButton>
          <CButton color="primary" onClick={parseConfirmedFile}>
            Yes, Parse File
          </CButton>
        </CModalFooter>
      </CModal>

      <CModal visible={helpVisible} onClose={() => setHelpVisible(false)} size="lg">
        <CModalHeader>
          <CModalTitle>CSV Game File Format</CModalTitle>
        </CModalHeader>
        <CModalBody>
          <p>The file must be UTF-8, headerless, and contain these six columns in order:</p>
          <div className="table-responsive">
            <CTable bordered small>
              <CTableHead>
                <CTableRow>
                  {GAME_COLUMNS.map((column) => (
                    <CTableHeaderCell key={column}>{column}</CTableHeaderCell>
                  ))}
                </CTableRow>
              </CTableHead>
              <CTableBody>
                <CTableRow>
                  {['2026-01-15', 'Central High', 'Lincoln High', '72', '68', '0'].map(
                    (value, index) => <CTableDataCell key={GAME_COLUMNS[index]}>{value}</CTableDataCell>,
                  )}
                </CTableRow>
              </CTableBody>
            </CTable>
          </div>
          <p className="mb-0">Use <code>0</code> for a home-field game and <code>999</code> for a neutral-site game.</p>
        </CModalBody>
        <CModalFooter>
          <CButton color="primary" onClick={() => setHelpVisible(false)}>Close</CButton>
        </CModalFooter>
      </CModal>
    </div>
  )
}

export default AddGames
