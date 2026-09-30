import React, { useEffect, useState } from 'react'
import {
  CAlert,
  CButton,
  CCol,
  CContainer,
  CForm,
  CFormInput,
  CFormLabel,
  CModal,
  CModalBody,
  CModalFooter,
  CModalHeader,
  CModalTitle,
  CRow,
} from '@coreui/react'
import { useSelector } from 'react-redux'
import Select from 'react-select'
import api from 'src/api'
import { formatDatasetName } from 'src/utils/displayNames'

const UpdateTeamName = () => {
  const sport = useSelector((state) => state.sport)
  const gender = useSelector((state) => state.gender)
  const level = useSelector((state) => state.level)
  const [newTeamName, setNewTeamName] = useState('')
  const [selectedTeam, setSelectedTeam] = useState(null)
  const [teamsOptions, setTeamsOptions] = useState([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState(false)
  const [updating, setUpdating] = useState(false)
  const [confirmationVisible, setConfirmationVisible] = useState(false)
  const [resultMessage, setResultMessage] = useState('')
  const [resultColor, setResultColor] = useState('info')
  const datasetName = formatDatasetName({ sport, gender, level })
  const trimmedNewTeamName = newTeamName.trim()
  const canSubmit =
    selectedTeam && trimmedNewTeamName && trimmedNewTeamName !== selectedTeam.label && !updating

  useEffect(() => {
    let isCurrentRequest = true

    const fetchTeamOptions = async () => {
      setSelectedTeam(null)
      setNewTeamName('')
      setTeamsOptions([])
      setLoadError(false)
      setResultMessage('')
      setConfirmationVisible(false)
      setLoading(true)

      try {
        const response = await api.get('/teams-ids/', {
          params: {
            sport_type: sport,
            gender,
            level,
          },
        })

        if (!isCurrentRequest) return

        if (response.status === 204 || response.data?.status === 204) {
          return
        }

        const teams = response.data?.data?.teams
        if (!Array.isArray(teams)) {
          throw new Error('Teams response did not contain a teams array')
        }

        setTeamsOptions(
          teams.map((team) => ({
            value: team.team_id,
            label: team.team_name,
          })),
        )
      } catch (error) {
        if (!isCurrentRequest) return

        console.error('Failed to retrieve team names and ids', error)
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

  const handleReviewUpdate = (event) => {
    event.preventDefault()
    if (canSubmit) setConfirmationVisible(true)
  }

  const handleUpdateTeamName = async () => {
    if (!canSubmit) return

    const currentTeam = selectedTeam
    const updatedName = trimmedNewTeamName
    setUpdating(true)
    setResultMessage('')

    try {
      const response = await api.put(
        `/update-name/${currentTeam.value}/${encodeURIComponent(updatedName)}`,
        {},
        {
          params: {
            sport_type: sport,
            gender,
            level,
          },
        },
      )

      if (response.data?.status !== 200) {
        throw new Error(response.data?.message || 'The team name could not be updated')
      }

      setTeamsOptions((options) =>
        options.map((option) =>
          option.value === currentTeam.value ? { ...option, label: updatedName } : option,
        ),
      )
      setResultColor('success')
      setResultMessage(
        response.data.message || `${currentTeam.label} was renamed to ${updatedName}`,
      )
      setSelectedTeam(null)
      setNewTeamName('')
      setConfirmationVisible(false)
    } catch (error) {
      console.error('Error when updating team name', error)
      setResultColor('danger')
      setResultMessage(
        error.response?.data?.detail || error.message || 'The team name could not be updated',
      )
      setConfirmationVisible(false)
    } finally {
      setUpdating(false)
    }
  }

  return (
    <CContainer className="mt-4">
      <CRow className="mb-3">
        <CCol>
          <h4>Update Team Name</h4>
        </CCol>
      </CRow>

      {loadError && <CAlert color="danger">Failed to Load {datasetName} Teams</CAlert>}
      {!loading && !loadError && teamsOptions.length === 0 && (
        <CAlert color="info">No {datasetName} Teams Found</CAlert>
      )}
      {resultMessage && <CAlert color={resultColor}>{resultMessage}</CAlert>}

      <CForm onSubmit={handleReviewUpdate}>
        <CRow className="g-3 align-items-end">
          <CCol md={5}>
            <CFormLabel htmlFor="current-team-name">Current Team Name</CFormLabel>
            <Select
              aria-label="Current Team Name"
              classNamePrefix="react-select"
              inputId="current-team-name"
              isClearable
              isDisabled={loading || loadError}
              isLoading={loading}
              isSearchable
              noOptionsMessage={() => 'No Teams Found'}
              onChange={setSelectedTeam}
              options={teamsOptions}
              placeholder="Select Team"
              value={selectedTeam}
            />
          </CCol>
          <CCol md={5}>
            <CFormLabel htmlFor="new-team-name">New Team Name</CFormLabel>
            <CFormInput
              id="new-team-name"
              maxLength={150}
              onChange={(event) => setNewTeamName(event.target.value)}
              placeholder="Enter new name"
              type="text"
              value={newTeamName}
            />
          </CCol>
          <CCol md={2}>
            <CButton color="primary" disabled={!canSubmit} type="submit">
              Update Team Name
            </CButton>
          </CCol>
        </CRow>
      </CForm>

      <CModal
        alignment="center"
        backdrop="static"
        onClose={() => !updating && setConfirmationVisible(false)}
        visible={confirmationVisible}
      >
        <CModalHeader closeButton={!updating}>
          <CModalTitle>Confirm Team Name Update</CModalTitle>
        </CModalHeader>
        <CModalBody>
          <p>
            Change <strong>{selectedTeam?.label}</strong> to{' '}
            <strong>{trimmedNewTeamName}</strong>?
          </p>
          <CAlert color="warning" className="mb-0">
            All instances of the current team name will be updated in team records, related
            games, uploaded game files, flagged games, and archived season data.
          </CAlert>
        </CModalBody>
        <CModalFooter>
          <CButton
            color="secondary"
            disabled={updating}
            onClick={() => setConfirmationVisible(false)}
            type="button"
          >
            Cancel
          </CButton>
          <CButton
            color="primary"
            disabled={updating}
            onClick={handleUpdateTeamName}
            type="button"
          >
            {updating ? 'Updating...' : 'Confirm Update'}
          </CButton>
        </CModalFooter>
      </CModal>
    </CContainer>
  )
}

export default UpdateTeamName
