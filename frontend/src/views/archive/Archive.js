import React, { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import {
  CAlert,
  CButton,
  CCol,
  CContainer,
  CFormInput,
  CFormSelect,
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
import { cilChevronRight, cilHistory } from '@coreui/icons'
import api from 'src/api'

const LoadingState = () => (
  <div className="d-flex justify-content-center p-5">
    <CSpinner />
  </div>
)

const ArchiveCatalog = ({ archives }) => {
  if (archives.length === 0) {
    return (
      <CAlert color="info">
        No season archives are available yet.
      </CAlert>
    )
  }

  return archives.map((archive) => (
    <section className="border-top py-4" key={archive.year} aria-labelledby={`year-${archive.year}`}>
      <div className="d-flex align-items-start justify-content-between gap-3 mb-3">
        <div>
          <h2 className="h4 mb-1" id={`year-${archive.year}`}>{archive.year} Season</h2>
          <div className="text-body-secondary">
            {archive.team_count} teams across {archive.dataset_count} rankings
          </div>
        </div>
        <CButton color="primary" variant="outline" as={Link} to={`/archives/${archive.year}`}>
          Open Season
        </CButton>
      </div>
      <nav className="list-group" aria-label={`${archive.year} archived rankings`}>
        {archive.datasets.map((dataset) => (
          <Link
            className="list-group-item list-group-item-action d-flex align-items-center justify-content-between gap-3 py-3"
            key={dataset.slug}
            to={`/archives/${archive.year}/${dataset.slug}`}
          >
            <span>
              <strong>{dataset.label}</strong>
              <span className="text-body-secondary ms-2">{dataset.team_count} teams</span>
            </span>
            <CIcon aria-hidden="true" icon={cilChevronRight} />
          </Link>
        ))}
      </nav>
    </section>
  ))
}

const ArchiveTable = ({ dataset, year }) => {
  const [searchTerm, setSearchTerm] = useState('')
  const teams = useMemo(() => {
    const normalizedSearch = searchTerm.trim().toLowerCase()
    if (!normalizedSearch) return dataset.teams
    return dataset.teams.filter((team) =>
      team.team_name.toLowerCase().includes(normalizedSearch),
    )
  }, [dataset, searchTerm])

  useEffect(() => {
    setSearchTerm('')
  }, [dataset.slug])

  return (
    <section aria-labelledby="archive-ranking-heading">
      <div className="d-flex flex-wrap align-items-end justify-content-between gap-3 mb-3">
        <div>
          <h2 className="h4 mb-1" id="archive-ranking-heading">
            {year} {dataset.label} Rankings
          </h2>
          <div className="text-body-secondary">{dataset.team_count} archived teams</div>
        </div>
        <CFormInput
          aria-label="Search archived teams"
          className="archive-search"
          onChange={(event) => setSearchTerm(event.target.value)}
          placeholder="Search teams"
          type="search"
          value={searchTerm}
        />
      </div>

      {teams.length === 0 ? (
        <CAlert color="info">No archived teams match this search.</CAlert>
      ) : (
        <div className="table-responsive border rounded">
          <CTable className="mb-0 align-middle">
            <CTableHead color="light">
              <CTableRow>
                <CTableHeaderCell scope="col">Id</CTableHeaderCell>
                <CTableHeaderCell scope="col">Rank</CTableHeaderCell>
                <CTableHeaderCell scope="col">Team</CTableHeaderCell>
                <CTableHeaderCell scope="col" className="text-end">Power</CTableHeaderCell>
                <CTableHeaderCell scope="col" className="text-end">Div. Rank</CTableHeaderCell>
                <CTableHeaderCell scope="col">Division</CTableHeaderCell>
                <CTableHeaderCell scope="col" className="text-end">W</CTableHeaderCell>
                <CTableHeaderCell scope="col" className="text-end">L</CTableHeaderCell>
              </CTableRow>
            </CTableHead>
            <CTableBody>
              {teams.map((team) => (
                <CTableRow key={team.id || team.team_name}>
                  <CTableDataCell>{team.id}</CTableDataCell>
                  <CTableDataCell className="fw-semibold text-primary">{team.rank}</CTableDataCell>
                  <CTableDataCell>{team.team_name}</CTableDataCell>
                  <CTableDataCell className="text-end">
                    {team.power === null ? '-' : Number(team.power).toFixed(2)}
                  </CTableDataCell>
                  <CTableDataCell className="text-end">{team.division_rank || '-'}</CTableDataCell>
                  <CTableDataCell>{team.division || '-'}</CTableDataCell>
                  <CTableDataCell className="text-end">{team.wins}</CTableDataCell>
                  <CTableDataCell className="text-end">{team.losses}</CTableDataCell>
                </CTableRow>
              ))}
            </CTableBody>
          </CTable>
        </div>
      )}
    </section>
  )
}

const Archive = () => {
  const { year, dataset: datasetSlug } = useParams()
  const navigate = useNavigate()
  const [requestStatus, setRequestStatus] = useState('loading')
  const [archives, setArchives] = useState([])
  const [archive, setArchive] = useState(null)

  useEffect(() => {
    let current = true

    const loadArchive = async () => {
      setRequestStatus('loading')
      try {
        const { data } = year
          ? await api.get(`/archives/${year}`)
          : await api.get('/archives/')
        if (!current) return

        if (year) {
          setArchive(data)
        } else {
          setArchives(Array.isArray(data?.archives) ? data.archives : [])
        }
        setRequestStatus('success')
      } catch (error) {
        if (!current) return
        console.error('Failed to load season archives', error)
        setRequestStatus('error')
      }
    }

    loadArchive()
    return () => {
      current = false
    }
  }, [year])

  const selectedDataset = useMemo(() => {
    if (!archive?.datasets?.length) return null
    return archive.datasets.find((dataset) => dataset.slug === datasetSlug) || archive.datasets[0]
  }, [archive, datasetSlug])

  if (requestStatus === 'loading') return <LoadingState />
  if (requestStatus === 'error') {
    return <CAlert color="danger">Failed to load season archives.</CAlert>
  }

  if (!year) {
    return (
      <CContainer className="py-4">
        <header className="d-flex align-items-center gap-3 mb-4">
          <CIcon icon={cilHistory} size="xl" />
          <div>
            <h1 className="h2 mb-1">Season Archives</h1>
            <div className="text-body-secondary">Published final rankings by season</div>
          </div>
        </header>
        <ArchiveCatalog archives={archives} />
      </CContainer>
    )
  }

  if (!archive || !selectedDataset) {
    return <CAlert color="info">No ranking datasets were archived for {year}.</CAlert>
  }

  return (
    <CContainer className="py-4">
      <header className="mb-4">
        <Link to="/archives" className="d-inline-block mb-2">All Seasons</Link>
        <div className="d-flex flex-wrap align-items-start justify-content-between gap-3">
          <div>
            <h1 className="h2 mb-1">{archive.year} Season Archive</h1>
            <div className="text-body-secondary">
              {archive.team_count} teams across {archive.dataset_count} rankings
            </div>
          </div>
          <CButton
            color="secondary"
            variant="outline"
            href={`/archive/${archive.year}/index.html`}
            target="_blank"
            rel="noreferrer"
          >
            Static HTML
          </CButton>
        </div>
      </header>

      <CRow className="g-4">
        <CCol lg={4} xl={3}>
          <label className="form-label fw-semibold" htmlFor="archive-dataset">
            {archive.year} Ranking
          </label>
          <CFormSelect
            id="archive-dataset"
            value={selectedDataset.slug}
            onChange={(event) => navigate(`/archives/${year}/${event.target.value}`)}
          >
            {archive.datasets.map((dataset) => (
              <option key={dataset.slug} value={dataset.slug}>{dataset.label}</option>
            ))}
          </CFormSelect>
          <a
            className="d-inline-block mt-3"
            href={selectedDataset.static_url}
            target="_blank"
            rel="noreferrer"
          >
            Open this static page
          </a>
        </CCol>
        <CCol lg={8} xl={9}>
          <ArchiveTable dataset={selectedDataset} year={archive.year} />
        </CCol>
      </CRow>
    </CContainer>
  )
}

export default Archive
