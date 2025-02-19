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

import admin from './../../assets/images/avatars/admin.png'

const AppHeaderDropdown = () => {
  return (
    <CDropdown variant="nav-item">
      <CDropdownToggle placement="bottom-end" className="py-0 pe-0" caret={false}>
        <CAvatar src={admin} size="md" />
      </CDropdownToggle>
        <CDropdownMenu className="pt-0" placement="bottom-end">
        <CDropdownHeader className="bg-body-secondary fw-semibold mb-2">Admin Login</CDropdownHeader>
        <CDropdownItem href="#/login">
          <CIcon icon={cilSettings} className='me-2' />
          Login
        </CDropdownItem>
        </CDropdownMenu>
    </CDropdown>
  )
}

export default AppHeaderDropdown
