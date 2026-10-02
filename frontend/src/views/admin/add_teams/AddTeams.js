import React, { useState } from 'react'
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
  CRow,
  CSpinner,
} from '@coreui/react'
import api from 'src/api'
import { formatDisplayName } from 'src/utils/displayNames'
import { US_STATES } from 'src/utils/usStates'

const TEAM_DATA_HEADERS = [
  'state',
  'short_name',
  'long_name',
  'division',
  'conference',
  'ranked',
]

const emptyTeam = {
  state: '',
  short_name: '',
  long_name: '',
  division: '',
  conference: '',
  ranked: 'yes',
}

const AddTeams = () => {
  const sport = useSelector((state) => state.sport)
  const gender = useSelector((state) => state.gender)
  const level = useSelector((state) => state.level)
  const [mode, setMode] = useState('upload')
  const [file, setFile] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [feedback, setFeedback] = useState(null)
  const [fileInputKey, setFileInputKey] = useState(0)
  const [manualTeam, setManualTeam] = useState(emptyTeam)
  const datasetName = [level, gender, sport].map(formatDisplayName).join(' ')
  const query = `sport_type=${sport}&gender=${gender}&level=${level}`

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (!file) return

    const formData = new FormData()
    formData.append('csv_file', file)
    setSubmitting(true)
    setFeedback(null)

    try {
      const { data } = await api.post(`/teams/upload/?${query}`, formData)
      const messages = [data.message]
      if (data.teams_failed?.length) {
        messages.push(...data.teams_failed.map(
          (team) => `${team.team_name}: ${team.reason}`,
        ))
      }
      setFeedback({ color: data.teams_failed?.length ? 'warning' : 'success', messages })
      setFile(null)
      setFileInputKey((key) => key + 1)
    } catch (error) {
      const detail = error.response?.data?.detail
      const messages = Array.isArray(detail?.errors)
        ? detail.errors
        : [detail?.message || detail || 'Failed to upload team data.']
      setFeedback({ color: 'danger', messages })
    } finally {
      setSubmitting(false)
    }
  }

  const updateManualTeam = (field, value) => {
    setManualTeam((current) => ({ ...current, [field]: value }))
  }

  const submitManualTeam = async (event) => {
    event.preventDefault()
    setSubmitting(true)
    setFeedback(null)

    const payload = {
      state: manualTeam.state.trim(),
      short_name: manualTeam.short_name.trim(),
      long_name: manualTeam.long_name.trim(),
      division: manualTeam.division.trim(),
      conference: manualTeam.conference.trim(),
      ranked: manualTeam.ranked === 'yes',
    }

    try {
      const { data } = await api.post(`/add_teams/?${query}`, [payload])
      if (data.added?.length) {
        setFeedback({ color: 'success', messages: ['Team added successfully'] })
        setManualTeam(emptyTeam)
      } else {
        const failure = data.skipped?.[0]
        setFeedback({
          color: 'warning',
          messages: [failure ? `${failure.team_name}: ${failure.reason}` : 'Team was not added.'],
        })
      }
    } catch (error) {
      const detail = error.response?.data?.detail
      setFeedback({
        color: 'danger',
        messages: [typeof detail === 'string' ? detail : 'Failed to add the team.'],
      })
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="mb-4">
      <h1 className="h3 mb-3">Add Teams</h1>
      <CButtonGroup role="group" aria-label="Add teams method" className="mb-4">
        <CButton
          color="primary"
          variant={mode === 'upload' ? undefined : 'outline'}
          onClick={() => setMode('upload')}
        >
          Upload Team File
        </CButton>
        <CButton
          color="primary"
          variant={mode === 'manual' ? undefined : 'outline'}
          onClick={() => setMode('manual')}
        >
          Add One Team
        </CButton>
      </CButtonGroup>

      {feedback && (
        <CAlert color={feedback.color} dismissible onClose={() => setFeedback(null)}>
          {feedback.messages.map((message) => <div key={message}>{message}</div>)}
        </CAlert>
      )}

      {mode === 'upload' ? (
        <CForm className="p-4 border rounded" onSubmit={handleSubmit}>
          <h2 className="h5 mb-3">Upload Team Data For {datasetName}</h2>
          <CFormInput
            key={fileInputKey}
            type="file"
            accept=".csv,text/csv"
            id="team-data-file"
            label="Choose Team Data CSV"
            onChange={(event) => {
              setFile(event.target.files?.[0] || null)
              setFeedback(null)
            }}
            disabled={submitting}
          />
          <p className="small text-body-secondary mt-2 mb-0">
            Required headers: {TEAM_DATA_HEADERS.join(', ')}
          </p>
          <CButton type="submit" color="primary" className="mt-3" disabled={!file || submitting}>
            {submitting && <CSpinner size="sm" className="me-2" />}
            Upload Team Data
          </CButton>
        </CForm>
      ) : (
        <CForm className="p-4 border rounded" onSubmit={submitManualTeam}>
          <h2 className="h5 mb-3">Add One Team For {datasetName}</h2>
          <CRow className="g-3">
            <CCol md={4}>
              <CFormLabel htmlFor="team-state">State</CFormLabel>
              <CFormSelect
                id="team-state"
                value={manualTeam.state}
                onChange={(event) => updateManualTeam('state', event.target.value)}
                required
              >
                <option value="" disabled>Select a state</option>
                {US_STATES.map((state) => (
                  <option key={state} value={state}>{state}</option>
                ))}
              </CFormSelect>
            </CCol>
            <CCol md={4}>
              <CFormInput
                id="team-short-name"
                label="Short Name"
                value={manualTeam.short_name}
                onChange={(event) => updateManualTeam('short_name', event.target.value)}
                required
              />
            </CCol>
            <CCol md={4}>
              <CFormInput
                id="team-long-name"
                label="Long Name"
                value={manualTeam.long_name}
                onChange={(event) => updateManualTeam('long_name', event.target.value)}
              />
            </CCol>
            <CCol md={4}>
              <CFormInput
                id="team-division"
                label="Division"
                value={manualTeam.division}
                onChange={(event) => updateManualTeam('division', event.target.value)}
              />
            </CCol>
            <CCol md={4}>
              <CFormInput
                id="team-conference"
                label="Conference"
                value={manualTeam.conference}
                onChange={(event) => updateManualTeam('conference', event.target.value)}
              />
            </CCol>
            <CCol md={4}>
              <CFormLabel htmlFor="team-ranked">Ranked</CFormLabel>
              <CFormSelect
                id="team-ranked"
                value={manualTeam.ranked}
                onChange={(event) => updateManualTeam('ranked', event.target.value)}
              >
                <option value="no">No</option>
                <option value="yes">Yes</option>
              </CFormSelect>
            </CCol>
          </CRow>
          <CButton type="submit" color="primary" className="mt-3" disabled={submitting}>
            {submitting && <CSpinner size="sm" className="me-2" />}
            Add Team
          </CButton>
        </CForm>
      )}
    </div>
  )
}

export default AddTeams
