import React from 'react'
import {
  CAvatar,
  // CBadge,
  CDropdown,
  // CDropdownDivider,
  CDropdownHeader,
  CDropdownItem,
  CDropdownMenu,
  CDropdownToggle,
} from '@coreui/react'
import {
  // cilBell,
  // cilLockLocked,
  cilSettings,
  // cilCog
} from '@coreui/icons'
import CIcon from '@coreui/icons-react'
import api from 'src/api'

import admin from './../../assets/images/avatars/admin.png'
import { useDispatch } from 'react-redux'

const AppHeaderDropdown = () => {
  const dispatch = useDispatch();

  const handleLogout = async () => {
    try {
      await api.post('/logout/', {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        credentials: 'include'
      });
      dispatch({ 'type': 'logout' });
    } catch (error) {
      console.log("An error has occured", error);
    }
  }


  return (
    <CDropdown variant="nav-item">
      <CDropdownToggle placement="bottom-end" className="py-0 pe-0" caret={false}>
        <CAvatar src={admin} size="md" />
      </CDropdownToggle>
        <CDropdownMenu className="pt-0" placement="bottom-end">
        <CDropdownHeader className="bg-body-secondary fw-semibold mb-2">Admin</CDropdownHeader>
        <CDropdownItem href="#/login">
          <CIcon icon={cilSettings} className='me-2' />
          Login
        </CDropdownItem>
        <CDropdownItem onClick={handleLogout} href='/'>
          <CIcon icon={cilSettings} className='me-2' />
          Logout
        </CDropdownItem>
        </CDropdownMenu>
    </CDropdown>
  )
}

export default AppHeaderDropdown
