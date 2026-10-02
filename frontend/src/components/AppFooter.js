import React from 'react'
import { CFooter } from '@coreui/react'

const AppFooter = () => {
  return (
    <CFooter className="px-4">
      <div className="ms-center">
        <span className="ms-1">&copy; {new Date().getUTCFullYear()} Packard Power Rankings.</span>
      </div>

    </CFooter>
  )
}
export default React.memo(AppFooter)
