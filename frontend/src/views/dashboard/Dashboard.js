import React from 'react'
import { CContainer, CRow, CCol } from '@coreui/react'

const Dashboard = () => {
  return (
    <CContainer className="py-5">
      <CRow className="justify-content-center">
        <CCol md={8} className="text-center">
          <h1>Welcome to Packard Power Rankings.</h1>
        </CCol>
      </CRow>
    </CContainer>
  )
}

export default Dashboard
