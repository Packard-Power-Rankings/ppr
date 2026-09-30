import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { useSelector } from 'react-redux'
import {
  CAlert,
  CButton,
  CCol,
  CModal,
  CModalBody,
  CModalFooter,
  CModalHeader,
  CModalTitle,
  CRow,
  CSpinner,
} from '@coreui/react'
import CIcon from '@coreui/icons-react'
import { cilChevronRight, cilHistory, cilTrash } from '@coreui/icons'
import api from 'src/api'
import { formatDisplayName } from 'src/utils/displayNames'

const ADMIN_TOOLS = [
  { label: 'Add Teams', to: '/admin/add_teams' },
  { label: 'Rankings', to: '/admin/ranking' },
  { label: 'Update Game', to: '/admin/update_game' },
  { label: 'Update Team Name', to: '/admin/update_team_name' },
  { label: 'Delete Game', to: '/admin/delete_game' },
  { label: 'Delete Team', to: '/admin/delete_team' },
]

const AdminDashboard = () => {
  const sport = useSelector((state) => state.sport)
  const gender = useSelector((state) => state.gender)
  const level = useSelector((state) => state.level)
  const [archiveDialog, setArchiveDialog] = useState(null)
  const [clearDialogVisible, setClearDialogVisible] = useState(false)
  const [feedback, setFeedback] = useState(null)
  const [checkingArchive, setCheckingArchive] = useState(false)
  const [archiving, setArchiving] = useState(false)
  const [clearing, setClearing] = useState(false)

  const datasetName = [
    formatDisplayName(level),
    formatDisplayName(gender),
    formatDisplayName(sport),
  ].join(' ')

  const handleArchivePrompt = async () => {
    setFeedback(null)
    setCheckingArchive(true)
    try {
      const { data } = await api.get('/archive-season/status')
      setArchiveDialog(data)
    } catch (error) {
      setFeedback({
        color: 'danger',
        message: error.response?.data?.detail || 'Failed to check the season archive.',
      })
    } finally {
      setCheckingArchive(false)
    }
  }

  const handleArchiveSeason = async () => {
    if (!archiveDialog) return

    setArchiving(true)
    try {
      const { data } = await api.post('/archive-season/', {}, {
        params: {
          year: archiveDialog.year,
          overwrite: archiveDialog.exists,
        },
      })
      setArchiveDialog(null)
      setFeedback({
        color: 'success',
        message: data.message,
        year: data.year,
      })
    } catch (error) {
      setArchiveDialog(null)
      setFeedback({
        color: 'danger',
        message: error.response?.data?.detail || 'Failed to archive the current season.',
      })
    } finally {
      setArchiving(false)
    }
  }

  const handleClearSeason = async () => {
    setClearing(true)
    setFeedback(null)
    try {
      const { data } = await api.delete('/clear-season/', {
        params: {
          sport_type: sport,
          gender,
          level,
        },
      })
      setClearDialogVisible(false)
      setFeedback({
        color: 'success',
        message: data.return_data || `${datasetName} season cleared.`,
      })
    } catch (error) {
      setClearDialogVisible(false)
      setFeedback({
        color: 'danger',
        message: error.response?.data?.detail || `Failed to clear the ${datasetName} season.`,
      })
    } finally {
      setClearing(false)
    }
  }

  return (
    <div className="pb-4">
      <header className="mb-4">
        <h1>PPR Admin Page</h1>
      </header>

      <section className="mb-5" aria-labelledby="admin-tools-heading">
        <h2 id="admin-tools-heading" className="h5 mb-3">Administration</h2>
        <CRow className="g-2">
          {ADMIN_TOOLS.map((tool) => (
            <CCol md={6} key={tool.to}>
              <Link
                to={tool.to}
                className="list-group-item list-group-item-action border rounded d-flex align-items-center justify-content-between px-3 py-3"
              >
                <span className="fw-semibold">{tool.label}</span>
                <CIcon icon={cilChevronRight} aria-hidden="true" />
              </Link>
            </CCol>
          ))}
        </CRow>
      </section>

      <section className="border-top pt-4" aria-labelledby="season-heading">
        <h2 id="season-heading" className="h5 mb-2">Season</h2>
        <p className="text-body-secondary mb-3">{datasetName}</p>
        <div className="d-flex flex-wrap gap-2">
          <CButton
            color="primary"
            onClick={handleArchivePrompt}
            disabled={checkingArchive || archiving || clearing}
          >
            {checkingArchive ? (
              <CSpinner className="me-2" size="sm" />
            ) : (
              <CIcon icon={cilHistory} className="me-2" />
            )}
            Archive Season
          </CButton>
          <CButton
            type="button"
            color="danger"
            onClick={() => {
              setFeedback(null)
              setClearDialogVisible(true)
            }}
            disabled={checkingArchive || archiving || clearing}
          >
            <CIcon icon={cilTrash} className="me-2" />
            Clear Season
          </CButton>
        </div>
      </section>

      {feedback && (
        <CAlert
          className="mt-4"
          color={feedback.color}
          dismissible
          onClose={() => setFeedback(null)}
        >
          {feedback.message}
          {feedback.year && (
            <Link className="alert-link ms-2" to={`/archives/${feedback.year}`}>
              View archive
            </Link>
          )}
        </CAlert>
      )}

      <CModal
        backdrop="static"
        visible={Boolean(archiveDialog)}
        onClose={() => !archiving && setArchiveDialog(null)}
      >
        <CModalHeader>
          <CModalTitle>
            {archiveDialog?.exists
              ? `Overwrite ${archiveDialog.year} Archive?`
              : `Archive ${archiveDialog?.year} Season?`}
          </CModalTitle>
        </CModalHeader>
        <CModalBody>
          {archiveDialog?.exists
            ? `A public archive for ${archiveDialog.year} already exists. Continuing will replace its static pages with the current rankings.`
            : 'This will publish the current rankings for every sport, gender, and level as public static pages.'}
        </CModalBody>
        <CModalFooter>
          <CButton
            color="secondary"
            variant="outline"
            onClick={() => setArchiveDialog(null)}
            disabled={archiving}
          >
            Cancel
          </CButton>
          <CButton
            color={archiveDialog?.exists ? 'danger' : 'primary'}
            onClick={handleArchiveSeason}
            disabled={archiving}
          >
            {archiving && <CSpinner className="me-2" size="sm" />}
            {archiveDialog?.exists ? 'Overwrite Archive' : 'Create Archive'}
          </CButton>
        </CModalFooter>
      </CModal>

      <CModal
        backdrop="static"
        visible={clearDialogVisible}
        onClose={() => !clearing && setClearDialogVisible(false)}
      >
        <CModalHeader>
          <CModalTitle>Clear {datasetName} Season?</CModalTitle>
        </CModalHeader>
        <CModalBody>
          The current season will be copied to previous-season storage before its games,
          records, and calculated rankings are reset. This action cannot be undone.
        </CModalBody>
        <CModalFooter>
          <CButton
            color="secondary"
            variant="outline"
            onClick={() => setClearDialogVisible(false)}
            disabled={clearing}
          >
            Cancel
          </CButton>
          <CButton color="danger" onClick={handleClearSeason} disabled={clearing}>
            {clearing && <CSpinner className="me-2" size="sm" />}
            Clear Season
          </CButton>
        </CModalFooter>
      </CModal>
    </div>
  )
}

export default AdminDashboard
