import React from 'react'
import { useSelector } from 'react-redux'
import { useLocation } from 'react-router-dom'
import { AppContent, AppSidebar, AppFooter, AppHeader, AdminHeader } from '../components/index'

const DefaultLayout = () => {
  const isAdmin = useSelector((state) => state.isAdmin);
  const location = useLocation();

  const isAdminLocation = location.pathname.startsWith('/admin');

  return (
    <div>
      <AppSidebar />
      <div className="wrapper d-flex flex-column min-vh-100">
        <AppHeader />
        {isAdmin && isAdminLocation && <AdminHeader />}
        <div className="body flex-grow-1">
          <AppContent />
        </div>
        <AppFooter />
      </div>
    </div>
  )
}

export default DefaultLayout
