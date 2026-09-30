import React, { Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { CContainer, CSpinner } from '@coreui/react'

// routes config
import routes from '../routes'
import RequireAdmin from './RequireAdmin'

const AppContent = () => {
  return (
    <CContainer className="px-4" lg>
      <Suspense fallback={<CSpinner color="primary" />}>
        <Routes>
          {routes.map((route, idx) => {
            if (!route.element) {
              return null
            }

            const RouteElement = route.element
            const element = route.admin ? (
              <RequireAdmin>
                <RouteElement />
              </RequireAdmin>
            ) : (
              <RouteElement />
            )

            return <Route key={idx} path={route.path} element={element} />
          })}
          <Route path="*" element={<Navigate to="/404" replace />} />
        </Routes>
      </Suspense>
    </CContainer>
  )
}

export default React.memo(AppContent)
