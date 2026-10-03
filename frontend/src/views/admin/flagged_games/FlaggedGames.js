import React, { useCallback, useEffect, useState } from 'react'
import {
  CAlert,
  CButton,
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
import CIcon from '@coreui/icons-react'
import { cilCheckCircle } from '@coreui/icons'
import { format } from 'date-fns'
import { Link } from 'react-router-dom'

import api from 'src/api'
import { formatDatasetName } from 'src/utils/displayNames'


const PAGE_SIZE = 50
const DESCRIPTION_PREVIEW_LENGTH = 120

const formatReportedAt = (value) => {
  if (!value) return 'Unknown'
  try {
    return format(new Date(value), 'MM-dd-yyyy hh:mm bbb')
  } catch (_error) {
    return 'Unknown'
  }
}

const FlaggedGames = () => {
  const [issues, setIssues] = useState([])
  const [count, setCount] = useState(0)
  const [skip, setSkip] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [feedback, setFeedback] = useState('')
  const [detailIssue, setDetailIssue] = useState(null)
  const [resolveIssue, setResolveIssue] = useState(null)
  const [resolving, setResolving] = useState(false)

  const loadIssues = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const response = await api.get('/flagged-games/', {
        params: { skip, limit: PAGE_SIZE },
      })
      setIssues(response.data?.issues || [])
      setCount(response.data?.count || 0)
    } catch (_error) {
      setError('Flagged game issues could not be loaded.')
    } finally {
      setLoading(false)
    }
  }, [skip])

  useEffect(() => {
    loadIssues()
  }, [loadIssues])

  const confirmResolve = async () => {
    if (!resolveIssue) return
    setResolving(true)
    setError('')
    try {
      await api.patch(`/flagged-games/${encodeURIComponent(resolveIssue.issue_id)}/resolve`)
      setFeedback('The game issue was marked as resolved.')
      setResolveIssue(null)
      window.dispatchEvent(new Event('flagged-issues-changed'))
      setCount((currentCount) => Math.max(0, currentCount - 1))
      if (issues.length === 1 && skip > 0) {
        setSkip(Math.max(0, skip - PAGE_SIZE))
      } else {
        setIssues((currentIssues) => currentIssues.filter(
          (issue) => issue.issue_id !== resolveIssue.issue_id,
        ))
      }
    } catch (requestError) {
      const detail = requestError.response?.data?.detail
      setError(typeof detail === 'string' ? detail : 'The game issue could not be resolved.')
    } finally {
      setResolving(false)
    }
  }

  return (
    <div className="pb-4">
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h1 className="h2 mb-0">Flagged Game Issues</h1>
        <span className="text-body-secondary">
          {count} unresolved {count === 1 ? 'issue' : 'issues'}
        </span>
      </div>

      {error && <CAlert color="danger">{error}</CAlert>}
      {feedback && (
        <CAlert color="success" dismissible onClose={() => setFeedback('')}>
          {feedback}
        </CAlert>
      )}

      {loading ? (
        <div className="d-flex justify-content-center p-5"><CSpinner /></div>
      ) : issues.length === 0 ? (
        <CAlert color="info">There are no unresolved game issues.</CAlert>
      ) : (
        <>
          <CTable align="middle" hover responsive>
            <CTableHead>
              <CTableRow>
                <CTableHeaderCell>Reported</CTableHeaderCell>
                <CTableHeaderCell>Dataset</CTableHeaderCell>
                <CTableHeaderCell>Game</CTableHeaderCell>
                <CTableHeaderCell>Issue</CTableHeaderCell>
                <CTableHeaderCell className="text-center">Resolve</CTableHeaderCell>
              </CTableRow>
            </CTableHead>
            <CTableBody>
              {issues.map((issue) => {
                const description = issue.description || 'No description was provided.'
                const isLong = description.length > DESCRIPTION_PREVIEW_LENGTH
                return (
                  <CTableRow key={issue.issue_id}>
                    <CTableDataCell>{formatReportedAt(issue.reported_at)}</CTableDataCell>
                    <CTableDataCell>{formatDatasetName(issue)}</CTableDataCell>
                    <CTableDataCell>
                      <Link
                        to="/admin/update_game"
                        state={{ flaggedIssue: issue }}
                        aria-label={`Update game ${issue.team1_name} vs ${issue.team2_name}`}
                      >
                        <div>{issue.team1_name} vs {issue.team2_name}</div>
                        <div className="small text-body-secondary">{issue.game_id}</div>
                      </Link>
                    </CTableDataCell>
                    <CTableDataCell style={{ minWidth: '18rem' }}>
                      {isLong ? (
                        <CButton
                          type="button"
                          color="link"
                          className="text-start p-0"
                          onClick={() => setDetailIssue(issue)}
                        >
                          {description.slice(0, DESCRIPTION_PREVIEW_LENGTH)}... View details
                        </CButton>
                      ) : description}
                    </CTableDataCell>
                    <CTableDataCell className="text-center">
                      <CButton
                        type="button"
                        color="success"
                        variant="ghost"
                        title="Mark issue as resolved"
                        aria-label={`Resolve issue for ${issue.team1_name} vs ${issue.team2_name}`}
                        onClick={() => setResolveIssue(issue)}
                      >
                        <CIcon icon={cilCheckCircle} size="lg" />
                      </CButton>
                    </CTableDataCell>
                  </CTableRow>
                )
              })}
            </CTableBody>
          </CTable>

          <div className="d-flex justify-content-between align-items-center mt-3">
            <CButton
              type="button"
              color="secondary"
              variant="outline"
              disabled={skip === 0}
              onClick={() => setSkip(Math.max(0, skip - PAGE_SIZE))}
            >
              Previous
            </CButton>
            <span className="small text-body-secondary">
              Showing {skip + 1}-{Math.min(skip + issues.length, count)} of {count}
            </span>
            <CButton
              type="button"
              color="secondary"
              variant="outline"
              disabled={skip + issues.length >= count}
              onClick={() => setSkip(skip + PAGE_SIZE)}
            >
              Next
            </CButton>
          </div>
        </>
      )}

      <CModal visible={Boolean(detailIssue)} onClose={() => setDetailIssue(null)}>
        <CModalHeader>
          <CModalTitle>Issue Details</CModalTitle>
        </CModalHeader>
        <CModalBody>
          <p className="fw-semibold mb-2">
            {detailIssue?.team1_name} vs {detailIssue?.team2_name}
          </p>
          <p className="mb-0" style={{ whiteSpace: 'pre-wrap' }}>
            {detailIssue?.description}
          </p>
        </CModalBody>
        <CModalFooter>
          <CButton color="primary" onClick={() => setDetailIssue(null)}>Close</CButton>
        </CModalFooter>
      </CModal>

      <CModal
        visible={Boolean(resolveIssue)}
        onClose={() => !resolving && setResolveIssue(null)}
      >
        <CModalHeader>
          <CModalTitle>Resolve Game Issue?</CModalTitle>
        </CModalHeader>
        <CModalBody>
          Mark the report for {resolveIssue?.team1_name} vs {resolveIssue?.team2_name} as
          resolved? It will be removed from the pending issue list.
        </CModalBody>
        <CModalFooter>
          <CButton
            color="secondary"
            variant="outline"
            disabled={resolving}
            onClick={() => setResolveIssue(null)}
          >
            Cancel
          </CButton>
          <CButton color="success" disabled={resolving} onClick={confirmResolve}>
            {resolving && <CSpinner className="me-2" size="sm" />}
            Resolve Issue
          </CButton>
        </CModalFooter>
      </CModal>
    </div>
  )
}

export default FlaggedGames
