import React, { useEffect, useState } from 'react'
import {
  CAlert,
  CButton,
  CCol,
  CContainer,
  CModal,
  CModalBody,
  CModalFooter,
  CModalHeader,
  CModalTitle,
  CRow,
} from '@coreui/react'
import Select from 'react-select'
import { useSelector } from 'react-redux'
import api from 'src/api'
import { formatDatasetName } from 'src/utils/displayNames'

const DeleteTeam = () => {
  const sport = useSelector((state) => state.sport)
  const gender = useSelector((state) => state.gender)
  const level = useSelector((state) => state.level)
  const [team, setTeam] = useState(null)
  const [teamsOptions, setTeamsOptions] = useState([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [resultMessage, setResultMessage] = useState('')
  const [resultColor, setResultColor] = useState('info')
  const [confirmationVisible, setConfirmationVisible] = useState(false)
  const datasetName = formatDatasetName({ sport, gender, level })

  useEffect(() => {
    let isCurrentRequest = true

    const fetchTeamOptions = async () => {
      setTeam(null)
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
          setTeamsOptions([])
          return
        }

        const teams = response.data?.data?.teams
        if (!Array.isArray(teams)) {
          throw new Error('Teams response did not contain a teams array')
        }

        setTeamsOptions(
          teams.map((item) => ({
            value: item.team_id,
            label: item.team_name,
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

  const handleTeamDelete = async () => {
    if (!team) return

    setDeleting(true)
    setResultMessage('')

    try {
      const response = await api.delete(
        `/delete-team/${encodeURIComponent(team.label)}/${team.value}/`,
        {
          params: {
            sport_type: sport,
            gender,
            level,
          },
        },
      )

      if (response.data?.status === 200) {
        setTeamsOptions((options) => options.filter((option) => option.value !== team.value))
        setResultColor('success')
        setResultMessage(response.data.message || `${team.label} was deleted`)
        setConfirmationVisible(false)
        setTeam(null)
      } else {
        setResultColor('danger')
        setResultMessage(response.data?.message || 'The team could not be deleted')
        setConfirmationVisible(false)
      }
    } catch (error) {
      console.error('Error when trying to delete team from database', error)
      setResultColor('danger')
      setResultMessage(error.response?.data?.detail || 'The team could not be deleted')
      setConfirmationVisible(false)
    } finally {
      setDeleting(false)
    }
  }

  return (
    <CContainer className="mt-4">
      <CRow className="mb-3">
        <CCol>
          <h4>Select a Team to Delete</h4>
        </CCol>
      </CRow>

      {loadError && <CAlert color="danger">Failed to Load {datasetName} Teams</CAlert>}
      {!loading && !loadError && teamsOptions.length === 0 && (
        <CAlert color="info">No {datasetName} Teams Found</CAlert>
      )}
      {resultMessage && <CAlert color={resultColor}>{resultMessage}</CAlert>}

      <CRow className="mb-3 g-3">
        <CCol md={8}>
          <Select
            classNamePrefix="react-select"
            isClearable
            isDisabled={loading || loadError}
            isLoading={loading}
            isSearchable
            noOptionsMessage={() => 'No Teams Found'}
            onChange={setTeam}
            options={teamsOptions}
            placeholder="Select Team"
            value={team}
          />
        </CCol>
        <CCol md={4}>
          <CButton
            color="danger"
            disabled={!team || deleting}
            onClick={() => setConfirmationVisible(true)}
            type="button"
          >
            Delete Team
          </CButton>
        </CCol>
      </CRow>

      <CModal
        alignment="center"
        backdrop="static"
        onClose={() => !deleting && setConfirmationVisible(false)}
        visible={confirmationVisible}
      >
        <CModalHeader closeButton={!deleting}>
          <CModalTitle>Delete Team?</CModalTitle>
        </CModalHeader>
        <CModalBody>
          <p>
            You are about to permanently delete <strong>{team?.label}</strong>.
          </p>
          <CAlert color="danger" className="mb-0">
            All team and game-related information will be deleted from the current dataset,
            uploaded game files, flagged games, and archived season data. This action cannot be
            undone.
          </CAlert>
        </CModalBody>
        <CModalFooter>
          <CButton
            color="secondary"
            disabled={deleting}
            onClick={() => setConfirmationVisible(false)}
            type="button"
          >
            Cancel
          </CButton>
          <CButton color="danger" disabled={deleting} onClick={handleTeamDelete} type="button">
            {deleting ? 'Deleting...' : 'Confirm Delete Team'}
          </CButton>
        </CModalFooter>
      </CModal>
    </CContainer>
  )
}

export default DeleteTeam
