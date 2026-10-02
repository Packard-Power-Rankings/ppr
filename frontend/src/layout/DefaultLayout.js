import React from 'react'
import { useSelector } from 'react-redux'
import { useLocation } from 'react-router-dom'
import { AppContent, AppSidebar, AppFooter, AppHeader, AdminHeader } from '../components/index'

const DefaultLayout = () => {
  const isAdmin = useSelector((state) => state.isAdmin && state.authReady);
  const location = useLocation();

  const isAdminLocation = location.pathname.startsWith('/admin');
  const isAdminDashboard = ['/admin', '/admin/'].includes(location.pathname);

  return (
    <div>
      <AppSidebar />
      <div className="wrapper d-flex flex-column min-vh-100">
        <AppHeader />
        {isAdmin && isAdminLocation && !isAdminDashboard && <AdminHeader />}
        <div className="body flex-grow-1">
          <AppContent />
        </div>
        <AppFooter />
      </div>
    </div>
  )
}

export default DefaultLayout
