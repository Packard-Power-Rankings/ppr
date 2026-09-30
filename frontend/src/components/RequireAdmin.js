import React from 'react'
import PropTypes from 'prop-types'
import { useSelector } from 'react-redux'
import { Navigate, useLocation } from 'react-router-dom'
import { CSpinner } from '@coreui/react'

const RequireAdmin = ({ children }) => {
  const authReady = useSelector((state) => state.authReady)
  const isAdmin = useSelector((state) => state.isAdmin)
  const location = useLocation()

  if (!authReady) {
    return (
      <div className="py-5 text-center">
        <CSpinner color="primary" />
      </div>
    )
  }

  if (!isAdmin) {
    return <Navigate to="/admin/login" replace state={{ from: location }} />
  }

  return children
}

RequireAdmin.propTypes = {
  children: PropTypes.node.isRequired,
}

export default RequireAdmin
