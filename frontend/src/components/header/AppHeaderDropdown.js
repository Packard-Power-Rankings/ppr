import React from 'react'
import {
    CDropdown,
    CDropdownHeader,
    CDropdownMenu,
    CDropdownToggle,
    CButton,
} from '@coreui/react'
import {
    cilSettings,
    cilShieldAlt
} from '@coreui/icons'
import CIcon from '@coreui/icons-react'

import { useSelector } from 'react-redux'
import { useNavigate } from 'react-router-dom'

import { logoutUser } from 'src/services/authService'

const AppHeaderDropdown = () => {
    const isAdmin = useSelector((state) => state.isAdmin && state.authReady);
    const navigate = useNavigate();

    const handleLogout = async () => {
        try {
            await logoutUser();
            navigate('/');
        } catch (error) {
            console.error("An error has occurred", error);
        }
    }

    return (
        <CDropdown variant="nav-item" autoClose="outside">
            <CDropdownToggle placement="bottom-end" caret={false}>
                <CIcon icon={cilShieldAlt} className='me-2' size='lg' />
            </CDropdownToggle>
            <CDropdownMenu
                className="pt-0 shadow-lg rounded border-0 p-3"
                placement="bottom-end"
                style={{ minWidth: '250px' }}
            >
                <CDropdownHeader className="bg-body-secondary fw-semibold mb-2 text-center">Admin</CDropdownHeader>

                {!isAdmin && (
                    <div className="d-flex justify-content-center">
                        <CButton color="primary" className="w-100" onClick={() => navigate('/admin/login')}>
                            <CIcon icon={cilSettings} className='me-2' />
                            Admin Login
                        </CButton>
                    </div>
                )}

                {isAdmin && (
                    <div className="d-flex justify-content-center">
                        <CButton color="danger" className="w-100" onClick={handleLogout}>
                            <CIcon icon={cilSettings} className='me-2' />
                            Logout
                        </CButton>
                    </div>
                )}
            </CDropdownMenu>
        </CDropdown>
    );
};

export default AppHeaderDropdown
