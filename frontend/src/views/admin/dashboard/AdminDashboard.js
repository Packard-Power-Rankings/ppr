import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { useSelector } from 'react-redux'
import {
  CAlert,
  CButton,
  CCol,
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
import CIcon from '@coreui/icons-react'
import { cilChevronRight, cilHistory, cilTrash } from '@coreui/icons'
import api from 'src/api'
import { formatDisplayName } from 'src/utils/displayNames'

const ADMIN_TOOLS = [
  { group: 'Game', label: 'Add Games', to: '/admin/add_games' },
  { group: 'Team', label: 'Add Teams', to: '/admin/add_teams' },
  { group: 'Team', label: 'Export Teams', to: '/admin/export_teams' },
  { group: 'Other', label: 'Ranking', to: '/admin/ranking' },
  { group: 'Other', label: 'Z-Score', to: '/admin/z_scores' },
  { group: 'Other', label: 'Resolve Flagged Issues', to: '/admin/flagged-games' },
  { group: 'Game', label: 'Update Game', to: '/admin/update_game' },
  { group: 'Team', label: 'Update Team', to: '/admin/update_team' },
  { group: 'Game', label: 'Delete Game', to: '/admin/delete_game' },
  { group: 'Team', label: 'Delete Team', to: '/admin/delete_team' },
]

const ADMIN_TOOL_GROUPS = ['Game', 'Team', 'Other']

const AdminDashboard = () => {
  const sport = useSelector((state) => state.sport)
  const gender = useSelector((state) => state.gender)
  const level = useSelector((state) => state.level)
  const [archiveDialog, setArchiveDialog] = useState(null)
  const [archiveSelectedDialogVisible, setArchiveSelectedDialogVisible] = useState(false)
  const [archiveSport, setArchiveSport] = useState(sport)
  const [archiveGender, setArchiveGender] = useState(gender)
  const [archiveLevel, setArchiveLevel] = useState(level)
  const [unarchivedResetDialog, setUnarchivedResetDialog] = useState(null)
  const [clearDialogVisible, setClearDialogVisible] = useState(false)
  const [resetAllDialogVisible, setResetAllDialogVisible] = useState(false)
  const [clearSport, setClearSport] = useState(sport)
  const [clearGender, setClearGender] = useState(gender)
  const [clearLevel, setClearLevel] = useState(level)
  const [feedback, setFeedback] = useState(null)
  const [checkingArchive, setCheckingArchive] = useState(null)
  const [checkingResetArchive, setCheckingResetArchive] = useState(null)
  const [archiving, setArchiving] = useState(false)
  const [clearing, setClearing] = useState(false)
  const [resettingAll, setResettingAll] = useState(false)
  const datasetName = [
    formatDisplayName(clearLevel),
    formatDisplayName(clearGender),
    formatDisplayName(clearSport),
  ].join(' ')

  const archiveDatasetName = [
    formatDisplayName(archiveLevel),
    formatDisplayName(archiveGender),
    formatDisplayName(archiveSport),
  ].join(' ')

  const handleClearPrompt = () => {
    setClearSport(sport)
    setClearGender(sport === 'football' ? 'mens' : gender)
    setClearLevel(level)
    setFeedback(null)
    setClearDialogVisible(true)
  }

  const handleResetAllPrompt = async () => {
    setFeedback(null)
    setCheckingResetArchive('all')
    try {
      const { data } = await api.get('/archive-season/status')
      if (!data.exists || data.complete === false) {
        setUnarchivedResetDialog({ target: 'all', year: data.year })
        return
      }
      setResetAllDialogVisible(true)
    } catch (error) {
      setFeedback({
        color: 'danger',
        message: error.response?.data?.detail || 'Failed to verify the current season archive.',
      })
    } finally {
      setCheckingResetArchive(null)
    }
  }

  const handleProceedWithoutArchive = () => {
    const resetTarget = unarchivedResetDialog?.target
    setUnarchivedResetDialog(null)
    if (resetTarget === 'selected') {
      resetSelectedSport()
    } else if (resetTarget === 'all') {
      setResetAllDialogVisible(true)
    }
  }

  const handleArchiveSelectedPrompt = () => {
    setArchiveSport(sport)
    setArchiveGender(sport === 'football' ? 'mens' : gender)
    setArchiveLevel(level)
    setFeedback(null)
    setArchiveSelectedDialogVisible(true)
  }

  const handleArchiveAllPrompt = async () => {
    setFeedback(null)
    setCheckingArchive('all')
    try {
      const { data } = await api.get('/archive-season/status')
      setArchiveDialog({ ...data, scope: 'all' })
    } catch (error) {
      setFeedback({
        color: 'danger',
        message: error.response?.data?.detail || 'Failed to check the season archive.',
      })
    } finally {
      setCheckingArchive(null)
    }
  }

  const archiveSeason = async (request) => {
    setArchiving(true)
    try {
      const selected = request.scope === 'selected'
      const { data } = await api.post(`/archive-season/${request.scope}/`, {}, {
        params: selected ? {
          year: request.year,
          overwrite: request.exists,
          sport_type: request.sport,
          gender: request.gender,
          level: request.level,
        } : {
          year: request.year,
          overwrite: request.exists,
        },
      })
      setArchiveDialog(null)
      setArchiveSelectedDialogVisible(false)
      setFeedback({
        color: 'success',
        message: data.message,
        year: data.year,
      })
    } catch (error) {
      setArchiveDialog(null)
      setArchiveSelectedDialogVisible(false)
      setFeedback({
        color: 'danger',
        message: error.response?.data?.detail || 'Failed to archive the selected season data.',
      })
    } finally {
      setArchiving(false)
    }
  }

  const handleArchiveSelected = async () => {
    setFeedback(null)
    setCheckingArchive('selected')
    const selection = {
      sport: archiveSport,
      gender: archiveGender,
      level: archiveLevel,
    }
    try {
      const { data } = await api.get('/archive-season/status/selected', {
        params: {
          sport_type: selection.sport,
          gender: selection.gender,
          level: selection.level,
        },
      })
      const request = { ...data, ...selection, scope: 'selected' }
      if (data.exists) {
        setArchiveSelectedDialogVisible(false)
        setArchiveDialog(request)
      } else {
        await archiveSeason(request)
      }
    } catch (error) {
      setArchiveSelectedDialogVisible(false)
      setFeedback({
        color: 'danger',
        message: error.response?.data?.detail || 'Failed to check the selected sport archive.',
      })
    } finally {
      setCheckingArchive(null)
    }
  }

  const resetSelectedSport = async () => {
    setClearing(true)
    setFeedback(null)
    try {
      const { data } = await api.delete('/clear-season/', {
        params: {
          sport_type: clearSport,
          gender: clearGender,
          level: clearLevel,
        },
      })
      setClearDialogVisible(false)
      setFeedback({
        color: 'success',
        message: data.return_data || `${datasetName} season reset.`,
      })
    } catch (error) {
      setClearDialogVisible(false)
      setFeedback({
        color: 'danger',
        message: error.response?.data?.detail || `Failed to reset the ${datasetName} season.`,
      })
    } finally {
      setClearing(false)
    }
  }

  const handleClearSeason = async () => {
    setFeedback(null)
    setCheckingResetArchive('selected')
    try {
      const { data } = await api.get('/archive-season/status/selected', {
        params: {
          sport_type: clearSport,
          gender: clearGender,
          level: clearLevel,
        },
      })
      if (!data.exists) {
        setClearDialogVisible(false)
        setUnarchivedResetDialog({
          target: 'selected',
          year: data.year,
          datasetName,
        })
        return
      }
      await resetSelectedSport()
    } catch (error) {
      setClearDialogVisible(false)
      setFeedback({
        color: 'danger',
        message: error.response?.data?.detail || 'Failed to verify the selected sport archive.',
      })
    } finally {
      setCheckingResetArchive(null)
    }
  }

  const handleResetAllSports = async () => {
    setResettingAll(true)
    setFeedback(null)
    try {
      const { data } = await api.delete('/reset-all-sports/')
      setResetAllDialogVisible(false)
      setFeedback({
        color: 'success',
        message: data.return_data || 'All sports data was reset.',
      })
    } catch (error) {
      setResetAllDialogVisible(false)
      setFeedback({
        color: 'danger',
        message: error.response?.data?.detail || 'Failed to reset all sports data.',
      })
    } finally {
      setResettingAll(false)
    }
  }

  const seasonActionBusy = Boolean(checkingArchive) || archiving || clearing || resettingAll ||
    Boolean(checkingResetArchive)

  return (
    <div className="pb-4">
      <header className="mb-4">
        <h1>PPR Admin Page</h1>
      </header>

      <section className="mb-5" aria-labelledby="admin-tools-heading">
        <h2 id="admin-tools-heading" className="h5 mb-3">Administration</h2>
        {ADMIN_TOOL_GROUPS.map((group) => (
          <div className="mb-4" key={group}>
            <h3 className="h6 mb-2">{group}</h3>
            <CRow className="g-2">
              {ADMIN_TOOLS.filter((tool) => tool.group === group).map((tool) => (
                <CCol md={4} key={tool.to}>
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
          </div>
        ))}
      </section>

      <section className="border-top pt-4" aria-labelledby="season-heading">
        <h2 id="season-heading" className="h5 mb-2">Season</h2>
        <div className="d-flex flex-wrap gap-2">
          <CButton
            type="button"
            color="primary"
            variant="outline"
            onClick={handleArchiveSelectedPrompt}
            disabled={seasonActionBusy}
          >
            <CIcon icon={cilHistory} className="me-2" />
            Archive Selected Sport
          </CButton>
          <CButton
            type="button"
            color="primary"
            variant="outline"
            onClick={handleArchiveAllPrompt}
            disabled={seasonActionBusy}
          >
            {checkingArchive === 'all' ? (
              <CSpinner className="me-2" size="sm" />
            ) : (
              <CIcon icon={cilHistory} className="me-2" />
            )}
            Archive All Sports
          </CButton>
          <CButton
            type="button"
            color="danger"
            variant="outline"
            onClick={handleClearPrompt}
            disabled={seasonActionBusy}
          >
            {checkingResetArchive === 'selected' ? (
              <CSpinner className="me-2" size="sm" />
            ) : (
              <CIcon icon={cilTrash} className="me-2" />
            )}
            Reset Selected Sport
          </CButton>
          <CButton
            type="button"
            color="danger"
            variant="outline"
            onClick={handleResetAllPrompt}
            disabled={seasonActionBusy}
          >
            {checkingResetArchive === 'all' ? (
              <CSpinner className="me-2" size="sm" />
            ) : (
              <CIcon icon={cilTrash} className="me-2" />
            )}
            Reset All Sports
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
        visible={archiveSelectedDialogVisible}
        onClose={() => !archiving && setArchiveSelectedDialogVisible(false)}
      >
        <CModalHeader>
          <CModalTitle>Archive {archiveDatasetName}?</CModalTitle>
        </CModalHeader>
        <CModalBody>
          <CRow className="g-3 mb-3">
            <CCol md={4}>
              <CFormLabel htmlFor="archive-season-sport">Sport</CFormLabel>
              <CFormSelect
                id="archive-season-sport"
                value={archiveSport}
                onChange={(event) => {
                  const nextSport = event.target.value
                  setArchiveSport(nextSport)
                  if (nextSport === 'football') setArchiveGender('mens')
                }}
              >
                <option value="football">Football</option>
                <option value="basketball">Basketball</option>
              </CFormSelect>
            </CCol>
            <CCol md={4}>
              <CFormLabel htmlFor="archive-season-gender">Gender</CFormLabel>
              <CFormSelect
                id="archive-season-gender"
                value={archiveGender}
                onChange={(event) => setArchiveGender(event.target.value)}
              >
                <option value="mens">Mens</option>
                <option value="womens" disabled={archiveSport === 'football'}>Womens</option>
              </CFormSelect>
            </CCol>
            <CCol md={4}>
              <CFormLabel htmlFor="archive-season-level">Level</CFormLabel>
              <CFormSelect
                id="archive-season-level"
                value={archiveLevel}
                onChange={(event) => setArchiveLevel(event.target.value)}
              >
                <option value="high_school">High School</option>
                <option value="college">College</option>
              </CFormSelect>
            </CCol>
          </CRow>
          <p className="mb-0">
            This publishes the current rankings for only this dataset. Other sports already
            stored in the same year archive will be preserved.
          </p>
        </CModalBody>
        <CModalFooter>
          <CButton
            color="secondary"
            variant="outline"
            onClick={() => setArchiveSelectedDialogVisible(false)}
            disabled={archiving || checkingArchive === 'selected'}
          >
            Cancel
          </CButton>
          <CButton
            color="primary"
            onClick={handleArchiveSelected}
            disabled={archiving || checkingArchive === 'selected'}
          >
            {(archiving || checkingArchive === 'selected') && (
              <CSpinner className="me-2" size="sm" />
            )}
            Archive Selected Sport
          </CButton>
        </CModalFooter>
      </CModal>

      <CModal
        backdrop="static"
        visible={Boolean(archiveDialog)}
        onClose={() => !archiving && setArchiveDialog(null)}
      >
        <CModalHeader>
          <CModalTitle>
            {archiveDialog?.scope === 'selected'
              ? `Overwrite ${archiveDialog.year} ${archiveDialog.dataset?.label || archiveDatasetName} Archive?`
              : archiveDialog?.exists
                ? `Overwrite ${archiveDialog.year} All Sports Archive?`
                : `Archive All Sports for ${archiveDialog?.year}?`}
          </CModalTitle>
        </CModalHeader>
        <CModalBody>
          {archiveDialog?.scope === 'selected'
            ? `The ${archiveDialog.dataset?.label || archiveDatasetName} rankings are already archived for ${archiveDialog.year}. Continuing will replace only this dataset and preserve the other archived sports.`
            : archiveDialog?.exists
              ? `A public archive for ${archiveDialog.year} already exists. Continuing will replace all of its static pages with the current rankings.`
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
            onClick={() => archiveDialog && archiveSeason(archiveDialog)}
            disabled={archiving}
          >
            {archiving && <CSpinner className="me-2" size="sm" />}
            {archiveDialog?.scope === 'selected'
              ? 'Overwrite Selected Archive'
              : archiveDialog?.exists
                ? 'Overwrite All Sports Archive'
                : 'Archive All Sports'}
          </CButton>
        </CModalFooter>
      </CModal>

      <CModal
        backdrop="static"
        visible={Boolean(unarchivedResetDialog)}
        onClose={() => setUnarchivedResetDialog(null)}
      >
        <CModalHeader>
          <CModalTitle>
            {unarchivedResetDialog?.target === 'selected'
              ? `${unarchivedResetDialog.year} ${unarchivedResetDialog.datasetName} Is Not Archived`
              : `${unarchivedResetDialog?.year} Complete Season Is Not Archived`}
          </CModalTitle>
        </CModalHeader>
        <CModalBody>
          {unarchivedResetDialog?.target === 'selected'
            ? `Resetting now will permanently remove the current ${unarchivedResetDialog.datasetName} data without archiving it.`
            : 'Resetting now will permanently remove current-season data without a complete all-sports archive.'}
          {' '}Do you want to proceed without archiving?
        </CModalBody>
        <CModalFooter>
          <CButton
            color="secondary"
            variant="outline"
            onClick={() => setUnarchivedResetDialog(null)}
          >
            Cancel
          </CButton>
          <CButton color="danger" onClick={handleProceedWithoutArchive}>
            Proceed Without Archiving
          </CButton>
        </CModalFooter>
      </CModal>

      <CModal
        backdrop="static"
        visible={clearDialogVisible}
        onClose={() => !clearing && setClearDialogVisible(false)}
      >
        <CModalHeader>
          <CModalTitle>Reset {datasetName} Season?</CModalTitle>
        </CModalHeader>
        <CModalBody>
          <CRow className="g-3 mb-3">
            <CCol md={4}>
              <CFormLabel htmlFor="clear-season-sport">Sport</CFormLabel>
              <CFormSelect
                id="clear-season-sport"
                value={clearSport}
                onChange={(event) => {
                  const nextSport = event.target.value
                  setClearSport(nextSport)
                  if (nextSport === 'football') setClearGender('mens')
                }}
              >
                <option value="football">Football</option>
                <option value="basketball">Basketball</option>
              </CFormSelect>
            </CCol>
            <CCol md={4}>
              <CFormLabel htmlFor="clear-season-gender">Gender</CFormLabel>
              <CFormSelect
                id="clear-season-gender"
                value={clearGender}
                onChange={(event) => setClearGender(event.target.value)}
              >
                <option value="mens">Mens</option>
                <option value="womens" disabled={clearSport === 'football'}>Womens</option>
              </CFormSelect>
            </CCol>
            <CCol md={4}>
              <CFormLabel htmlFor="clear-season-level">Level</CFormLabel>
              <CFormSelect
                id="clear-season-level"
                value={clearLevel}
                onChange={(event) => setClearLevel(event.target.value)}
              >
                <option value="high_school">High School</option>
                <option value="college">College</option>
              </CFormSelect>
            </CCol>
          </CRow>
          <p className="mb-0">
            Wins and losses will return to zero, and canonical current-season games and source
            uploads will be removed. Ranking values and each team&apos;s five most recent game
            records will be preserved. The existing season archive will not be changed. This
            action cannot be undone.
          </p>
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
          <CButton
            color="danger"
            onClick={handleClearSeason}
            disabled={clearing || checkingResetArchive === 'selected'}
          >
            {(clearing || checkingResetArchive === 'selected') && (
              <CSpinner className="me-2" size="sm" />
            )}
            Reset Selected Sport
          </CButton>
        </CModalFooter>
      </CModal>

      <CModal
        backdrop="static"
        visible={resetAllDialogVisible}
        onClose={() => !resettingAll && setResetAllDialogVisible(false)}
      >
        <CModalHeader>
          <CModalTitle>Reset All Sports?</CModalTitle>
        </CModalHeader>
        <CModalBody>
          Wins and losses will return to zero for every sport, and canonical current-season
          games and source uploads will be removed. Ranking values and each team&apos;s five most
          recent game records will be preserved. The existing season archive will not be
          changed. This action cannot be undone.
        </CModalBody>
        <CModalFooter>
          <CButton
            color="secondary"
            variant="outline"
            onClick={() => setResetAllDialogVisible(false)}
            disabled={resettingAll}
          >
            Cancel
          </CButton>
          <CButton color="danger" onClick={handleResetAllSports} disabled={resettingAll}>
            {resettingAll && <CSpinner className="me-2" size="sm" />}
            Reset All Sports
          </CButton>
        </CModalFooter>
      </CModal>
    </div>
  )
}

export default AdminDashboard
