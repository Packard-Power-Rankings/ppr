import React, { useEffect, useState } from 'react'
import {
  CAlert,
  CButton,
  CCol,
  CContainer,
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
} from '@coreui/react'
import { useSelector } from 'react-redux'
import Select from 'react-select'
import api from 'src/api'
import { formatDatasetName } from 'src/utils/displayNames'
import { US_STATES } from 'src/utils/usStates'

const emptyForm = {
  short_name: '',
  long_name: '',
  state: '',
  division: '',
  conference: '',
  ranked: false,
}

const getTeamForm = (team) => ({
  short_name: team.short_name || team.team_name || '',
  long_name: team.long_name || '',
  state: team.state || '',
  division: team.division || '',
  conference: team.conference || '',
  ranked: Boolean(team.ranked),
})

const UpdateTeam = () => {
  const sport = useSelector((state) => state.sport)
  const gender = useSelector((state) => state.gender)
  const level = useSelector((state) => state.level)
  const [teamsOptions, setTeamsOptions] = useState([])
  const [selectedTeam, setSelectedTeam] = useState(null)
  const [form, setForm] = useState(emptyForm)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState(false)
  const [saving, setSaving] = useState(false)
  const [confirmationVisible, setConfirmationVisible] = useState(false)
  const [feedback, setFeedback] = useState(null)
  const datasetName = formatDatasetName({ sport, gender, level })
  const hasChanges = selectedTeam && Object.keys(form).some(
    (field) => form[field] !== getTeamForm(selectedTeam)[field],
  )
  const canSubmit = Boolean(
    selectedTeam && form.short_name.trim() && hasChanges && !saving,
  )
  const isRenaming = selectedTeam &&
    form.short_name.trim() !== (selectedTeam.team_name || selectedTeam.short_name)

  useEffect(() => {
    let isCurrentRequest = true

    const fetchTeamOptions = async () => {
      setTeamsOptions([])
      setSelectedTeam(null)
      setForm(emptyForm)
      setFeedback(null)
      setLoadError(false)
      setLoading(true)

      try {
        const response = await api.get('/teams-ids/', {
          params: { sport_type: sport, gender, level },
        })
        if (!isCurrentRequest) return

        if (response.status === 204 || response.data?.status === 204) return

        const teams = response.data?.data?.teams
        if (!Array.isArray(teams)) {
          throw new Error('Teams response did not contain a teams array')
        }

        setTeamsOptions(teams.map((team) => ({
          ...team,
          value: team.team_id,
          label: team.team_name,
        })))
      } catch (error) {
        if (!isCurrentRequest) return
        console.error('Failed to retrieve team information', error)
        setLoadError(true)
      } finally {
        if (isCurrentRequest) setLoading(false)
      }
    }

    fetchTeamOptions()
    return () => {
      isCurrentRequest = false
    }
  }, [sport, gender, level])

  const selectTeam = (team) => {
    setSelectedTeam(team)
    setForm(team ? getTeamForm(team) : emptyForm)
    setFeedback(null)
  }

  const updateField = (field, value) => {
    setForm((current) => ({ ...current, [field]: value }))
    setFeedback(null)
  }

  const handleReviewUpdate = (event) => {
    event.preventDefault()
    if (canSubmit) setConfirmationVisible(true)
  }

  const saveTeam = async () => {
    if (!canSubmit) return

    const updatedForm = {
      ...form,
      short_name: form.short_name.trim(),
      long_name: form.long_name.trim(),
      division: form.division.trim(),
      conference: form.conference.trim(),
    }
    setSaving(true)
    setFeedback(null)

    try {
      const response = await api.put(
        `/update-team/${selectedTeam.value}`,
        updatedForm,
        { params: { sport_type: sport, gender, level } },
      )
      if (response.data?.status !== 200) {
        throw new Error(response.data?.message || 'Team information could not be updated')
      }

      const updatedTeam = {
        ...selectedTeam,
        ...updatedForm,
        team_name: updatedForm.short_name,
        label: updatedForm.short_name,
      }
      setTeamsOptions((options) => options.map((team) =>
        team.value === updatedTeam.value ? updatedTeam : team,
      ))
      setSelectedTeam(updatedTeam)
      setForm(updatedForm)
      setConfirmationVisible(false)
      setFeedback({
        color: 'success',
        message: response.data.message || `${updatedForm.short_name} was updated`,
      })
    } catch (error) {
      console.error('Error updating team information', error)
      setConfirmationVisible(false)
      setFeedback({
        color: 'danger',
        message: error.response?.data?.detail || error.message || 'Team information could not be updated',
      })
    } finally {
      setSaving(false)
    }
  }

  return (
    <CContainer className="mt-4">
      <h1 className="h3 mb-3">Update Team</h1>
      <p className="text-body-secondary">{datasetName}</p>

      {loadError && <CAlert color="danger">Failed to load {datasetName} teams.</CAlert>}
      {!loading && !loadError && teamsOptions.length === 0 && (
        <CAlert color="info">No {datasetName} teams found.</CAlert>
      )}
      {feedback && <CAlert color={feedback.color}>{feedback.message}</CAlert>}

      <CRow className="mb-4">
        <CCol md={8} lg={6}>
          <CFormLabel htmlFor="update-team-search">Search Team</CFormLabel>
          <Select
            aria-label="Search Team"
            classNamePrefix="react-select"
            inputId="update-team-search"
            isClearable
            isDisabled={loading || loadError}
            isLoading={loading}
            isSearchable
            noOptionsMessage={() => 'No Teams Found'}
            onChange={selectTeam}
            options={teamsOptions}
            placeholder="Select a team"
            value={selectedTeam}
          />
        </CCol>
      </CRow>

      <CForm onSubmit={handleReviewUpdate}>
        <CRow className="g-3">
          <CCol md={6} lg={4}>
            <CFormInput
              id="update-team-short-name"
              label="Short Name"
              maxLength={150}
              disabled={!selectedTeam || saving}
              onChange={(event) => updateField('short_name', event.target.value)}
              required
              value={form.short_name}
            />
          </CCol>
          <CCol md={6} lg={4}>
            <CFormInput
              id="update-team-long-name"
              label="Long Name"
              maxLength={200}
              disabled={!selectedTeam || saving}
              onChange={(event) => updateField('long_name', event.target.value)}
              value={form.long_name}
            />
          </CCol>
          <CCol md={6} lg={4}>
            <CFormLabel htmlFor="update-team-state">State</CFormLabel>
            <CFormSelect
              id="update-team-state"
              disabled={!selectedTeam || saving}
              onChange={(event) => updateField('state', event.target.value)}
              value={form.state}
            >
              <option value="">Not set</option>
              {form.state && !US_STATES.includes(form.state) && (
                <option value={form.state}>{form.state}</option>
              )}
              {US_STATES.map((stateName) => (
                <option key={stateName} value={stateName}>{stateName}</option>
              ))}
            </CFormSelect>
          </CCol>
          <CCol md={6} lg={4}>
            <CFormInput
              id="update-team-division"
              label="Division"
              maxLength={100}
              disabled={!selectedTeam || saving}
              onChange={(event) => updateField('division', event.target.value)}
              value={form.division}
            />
          </CCol>
          <CCol md={6} lg={4}>
            <CFormInput
              id="update-team-conference"
              label="Conference"
              maxLength={150}
              disabled={!selectedTeam || saving}
              onChange={(event) => updateField('conference', event.target.value)}
              value={form.conference}
            />
          </CCol>
          <CCol md={6} lg={4}>
            <CFormLabel htmlFor="update-team-ranked">Ranked</CFormLabel>
            <CFormSelect
              id="update-team-ranked"
              disabled={!selectedTeam || saving}
              onChange={(event) => updateField('ranked', event.target.value === 'true')}
              value={String(form.ranked)}
            >
              <option value="true">Yes</option>
              <option value="false">No</option>
            </CFormSelect>
          </CCol>
        </CRow>
        <CButton
          className="mt-3"
          color="primary"
          disabled={!canSubmit}
          type="submit"
        >
          Save Team Information
        </CButton>
      </CForm>

      <CModal
        alignment="center"
        backdrop="static"
        onClose={() => !saving && setConfirmationVisible(false)}
        visible={confirmationVisible}
      >
        <CModalHeader closeButton={!saving}>
          <CModalTitle>Confirm Team Update</CModalTitle>
        </CModalHeader>
        <CModalBody>
          {isRenaming ? (
            <>
              <p>
                Rename <strong>{selectedTeam?.team_name}</strong> to{' '}
                <strong>{form.short_name.trim()}</strong> and save the other changes?
              </p>
              <CAlert color="warning" className="mb-0">
                The short name is used in team records, related games, flagged games, and
                archived season data.
              </CAlert>
            </>
          ) : 'Save the updated information for this team?'}
        </CModalBody>
        <CModalFooter>
          <CButton
            color="secondary"
            disabled={saving}
            onClick={() => setConfirmationVisible(false)}
            type="button"
          >
            Cancel
          </CButton>
          <CButton color="primary" disabled={saving} onClick={saveTeam} type="button">
            {saving && <CSpinner size="sm" className="me-2" />}
            {saving ? 'Saving...' : 'Confirm Update'}
          </CButton>
        </CModalFooter>
      </CModal>
    </CContainer>
  )
}

export default UpdateTeam