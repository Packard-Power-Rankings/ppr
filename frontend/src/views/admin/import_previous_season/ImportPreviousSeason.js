import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { useSelector } from 'react-redux'
import {
  CAlert,
  CButton,
  CForm,
  CFormInput,
  CModal,
  CModalBody,
  CModalFooter,
  CModalHeader,
  CModalTitle,
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

const ImportPreviousSeason = () => {
  const sport = useSelector((state) => state.sport)
  const gender = useSelector((state) => state.gender)
  const level = useSelector((state) => state.level)
  const [file, setFile] = useState(null)
  const [fileInputKey, setFileInputKey] = useState(0)
  const [confirmVisible, setConfirmVisible] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [feedback, setFeedback] = useState(null)
  const [result, setResult] = useState(null)
  const datasetName = [level, gender, sport].map(formatDisplayName).join(' ')
  const hasFlaggedRows = Boolean(result?.teams_flagged_count || result?.flagged_teams?.length)
  const hasWarnings = Boolean(result?.warnings?.length)

  const reviewImport = (event) => {
    event.preventDefault()
    if (!file) return
    setFeedback(null)
    setResult(null)
    setConfirmVisible(true)
  }

  const importSeason = async () => {
    const formData = new FormData()
    formData.append('csv_file', file)
    setSubmitting(true)
    setFeedback(null)

    try {
      const { data } = await api.post('/previous-season/import/', formData, {
        params: {
          sport_type: sport,
          gender,
          level,
        },
      })
      setResult(data)
      setFeedback({
        color: data.teams_flagged_count || data.warnings?.length ? 'warning' : 'success',
        messages: [data.message],
      })
      setFile(null)
      setFileInputKey((key) => key + 1)
      setConfirmVisible(false)
    } catch (error) {
      const detail = error.response?.data?.detail
      const messages = Array.isArray(detail?.errors)
        ? detail.errors
        : [detail?.message || detail || 'Failed to import previous-season rankings.']
      setFeedback({ color: 'danger', messages })
      setConfirmVisible(false)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="mb-4">
      <h1 className="h3 mb-3">Import Previous Season</h1>

      {feedback && (
        <CAlert color={feedback.color} dismissible onClose={() => setFeedback(null)}>
          {feedback.messages.map((message) => <div key={message}>{message}</div>)}
        </CAlert>
      )}

      <CForm className="p-4 border rounded" onSubmit={reviewImport}>
        <h2 className="h5 mb-3">Final Rankings For {datasetName}</h2>
        <CFormInput
          key={fileInputKey}
          type="file"
          accept=".csv,text/csv"
          id="previous-season-file"
          label="Choose Final Season Ranking CSV"
          onChange={(event) => {
            setFile(event.target.files?.[0] || null)
            setFeedback(null)
            setResult(null)
          }}
          disabled={submitting}
        />
        <CButton type="submit" color="primary" className="mt-3" disabled={!file || submitting}>
          Review Import
        </CButton>
      </CForm>

      {result && (
        <section className="mt-4" aria-labelledby="import-result-heading">
          <h2 id="import-result-heading" className="h5">Import Result</h2>
          <dl className="row mb-3">
            <dt className="col-sm-3">File</dt>
            <dd className="col-sm-9">{result.source_filename}</dd>
            <dt className="col-sm-3">Updated</dt>
            <dd className="col-sm-9">{result.teams_updated_count}</dd>
            <dt className="col-sm-3">Flagged</dt>
            <dd className="col-sm-9">{result.teams_flagged_count}</dd>
          </dl>

          {(hasFlaggedRows || hasWarnings) && (
            <CAlert color="warning" className="mb-4">
              <h3 className="h6 alert-heading">Action Needed</h3>
              <p className="mb-2">
                Rows below were not imported cleanly. Before continuing to archive and reset:
              </p>
              <ol className="mb-0">
                {hasFlaggedRows && (
                  <li>
                    For each flagged row, make the legacy team ID match exactly one team&apos;s
                    Short Name: correct the ID in the CSV, fix the team&apos;s Short Name
                    in <Link to="/admin/update_team">Update Team</Link>, or add the missing team
                    in <Link to="/admin/add_teams">Add Teams</Link>.
                  </li>
                )}
                {hasWarnings && (
                  <li>
                    For each warning, correct the recent opponent IDs in the CSV or add the
                    missing opponent teams in <Link to="/admin/add_teams">Add Teams</Link>.
                    Unknown opponents were saved as 0.
                  </li>
                )}
                <li>
                  Import the corrected file again. Matched teams are overwritten, so
                  re-importing is safe.
                </li>
              </ol>
            </CAlert>
          )}

          {result.flagged_teams?.length > 0 && (
            <div className="table-responsive mb-4">
              <h3 className="h6">Flagged Team Rows</h3>
              <CTable striped>
                <CTableHead>
                  <CTableRow>
                    <CTableHeaderCell scope="col">Row</CTableHeaderCell>
                    <CTableHeaderCell scope="col">Legacy Team ID</CTableHeaderCell>
                    <CTableHeaderCell scope="col">Issue</CTableHeaderCell>
                  </CTableRow>
                </CTableHead>
                <CTableBody>
                  {result.flagged_teams.map((team) => (
                    <CTableRow key={`${team.row}-${team.team_id}`}>
                      <CTableDataCell>{team.row}</CTableDataCell>
                      <CTableDataCell>{team.team_id}</CTableDataCell>
                      <CTableDataCell>{team.reason}</CTableDataCell>
                    </CTableRow>
                  ))}
                </CTableBody>
              </CTable>
            </div>
          )}

          {result.warnings?.length > 0 && (
            <div className="table-responsive mb-4">
              <h3 className="h6">Import Warnings</h3>
              <CTable striped>
                <CTableHead>
                  <CTableRow>
                    <CTableHeaderCell scope="col">Row</CTableHeaderCell>
                    <CTableHeaderCell scope="col">Legacy Team ID</CTableHeaderCell>
                    <CTableHeaderCell scope="col">Warning</CTableHeaderCell>
                  </CTableRow>
                </CTableHead>
                <CTableBody>
                  {result.warnings.map((warning) => (
                    <CTableRow key={`${warning.row}-${warning.team_id}-${warning.reason}`}>
                      <CTableDataCell>{warning.row}</CTableDataCell>
                      <CTableDataCell>{warning.team_id}</CTableDataCell>
                      <CTableDataCell>{warning.reason}</CTableDataCell>
                    </CTableRow>
                  ))}
                </CTableBody>
              </CTable>
            </div>
          )}

          <Link className="btn btn-primary" to="/admin">
            Continue To Archive And Reset
          </Link>
        </section>
      )}

      <CModal
        backdrop="static"
        visible={confirmVisible}
        onClose={() => !submitting && setConfirmVisible(false)}
      >
        <CModalHeader>
          <CModalTitle>Import {datasetName} Final Rankings?</CModalTitle>
        </CModalHeader>
        <CModalBody>
          <p><strong>File:</strong> {file?.name}</p>
          <p className="mb-0">
            Matched team standings will be replaced. Rows whose legacy team ID does not match
            an existing Short Name will be flagged and skipped. Teams, games, uploads, and
            archives will not be deleted.
          </p>
        </CModalBody>
        <CModalFooter>
          <CButton
            color="secondary"
            variant="outline"
            onClick={() => setConfirmVisible(false)}
            disabled={submitting}
          >
            Cancel
          </CButton>
          <CButton color="primary" onClick={importSeason} disabled={submitting}>
            {submitting && <CSpinner size="sm" className="me-2" />}
            Import Previous Season
          </CButton>
        </CModalFooter>
      </CModal>
    </div>
  )
}

export default ImportPreviousSeason
