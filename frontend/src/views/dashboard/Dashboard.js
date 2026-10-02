import React from 'react'
import { Link } from 'react-router-dom'
import { CCol, CContainer, CRow } from '@coreui/react'
import CIcon from '@coreui/icons-react'
import { cilAmericanFootball, cilBasketball, cilChevronRight, cilHistory } from '@coreui/icons'

const sportSections = [
  {
    name: 'Football',
    icon: cilAmericanFootball,
    links: [
      {
        label: 'Mens High School Football',
        to: '/football/mens/high_school',
      },
      {
        label: 'Mens College Football',
        to: '/football/mens/college',
      },
    ],
  },
  {
    name: 'Basketball',
    icon: cilBasketball,
    links: [
      {
        label: 'Mens High School Basketball',
        to: '/basketball/mens/high_school',
      },
      {
        label: 'Mens College Basketball',
        to: '/basketball/mens/college',
      },
      {
        label: 'Womens High School Basketball',
        to: '/basketball/womens/high_school',
      },
      {
        label: 'Womens College Basketball',
        to: '/basketball/womens/college',
      },
    ],
  },
]

const Dashboard = () => {
  return (
    <CContainer className="py-4">
      <header className="mb-4">
        <h1>Welcome to Packard Power Rankings.</h1>
      </header>

      <section aria-labelledby="rankings-heading">
        <h2 id="rankings-heading" className="h4 mb-3">
          Current Rankings
        </h2>
        <CRow className="g-4">
          {sportSections.map((section) => (
            <CCol md={6} key={section.name}>
              <h3 className="h6 d-flex align-items-center gap-2 mb-2">
                <CIcon icon={section.icon} />
                {section.name}
              </h3>
              <nav
                className="list-group"
                aria-label={`Current ${section.name} rankings`}
              >
                {section.links.map((link) => (
                  <Link
                    className="list-group-item list-group-item-action d-flex align-items-center justify-content-between gap-3 py-3"
                    key={link.to}
                    to={link.to}
                  >
                    <span>{link.label}</span>
                    <CIcon aria-hidden="true" icon={cilChevronRight} />
                  </Link>
                ))}
              </nav>
            </CCol>
          ))}
        </CRow>
      </section>

      <section className="border-top mt-5 pt-4" aria-labelledby="archive-heading">
        <h2 id="archive-heading" className="h4 mb-3">Archive</h2>
        <nav className="list-group" aria-label="Season archives">
          <Link
            className="list-group-item list-group-item-action d-flex align-items-center justify-content-between gap-3 py-3"
            to="/archives"
          >
            <span className="d-flex align-items-center gap-2">
              <CIcon icon={cilHistory} />
              Season Archives
            </span>
            <CIcon aria-hidden="true" icon={cilChevronRight} />
          </Link>
        </nav>
      </section>

    </CContainer>
  )
}

export default Dashboard
