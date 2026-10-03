import React, { useCallback, useEffect, useState } from 'react'
import {
    CBadge,
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

import api from 'src/api'
import { logoutUser } from 'src/services/authService'

const AppHeaderDropdown = () => {
    const isAdmin = useSelector((state) => state.isAdmin && state.authReady);
    const navigate = useNavigate();
    const [issueCount, setIssueCount] = useState(0);

    const loadIssueCount = useCallback(async () => {
        if (!isAdmin) {
            setIssueCount(0);
            return;
        }
        try {
            const response = await api.get('/flagged-games/count');
            setIssueCount(Number(response.data?.count) || 0);
        } catch (_error) {
            setIssueCount(0);
        }
    }, [isAdmin]);

    useEffect(() => {
        loadIssueCount();
        if (!isAdmin) return undefined;

        const interval = window.setInterval(loadIssueCount, 60000);
        window.addEventListener('flagged-issues-changed', loadIssueCount);
        return () => {
            window.clearInterval(interval);
            window.removeEventListener('flagged-issues-changed', loadIssueCount);
        };
    }, [isAdmin, loadIssueCount]);

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
            <CDropdownToggle
                placement="bottom-end"
                caret={false}
                aria-label={issueCount > 0
                    ? `Admin menu, ${issueCount} unresolved game issues`
                    : 'Admin menu'}
            >
                <span className="position-relative d-inline-flex me-2">
                    <CIcon icon={cilShieldAlt} size='lg' />
                    {issueCount > 0 && (
                        <CBadge
                            color="danger"
                            shape="rounded-pill"
                            className="position-absolute top-0 start-100 translate-middle"
                            style={{ fontSize: '0.62rem' }}
                        >
                            {issueCount > 99 ? '99+' : issueCount}
                        </CBadge>
                    )}
                </span>
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
                    <div className="d-grid gap-2">
                        <CButton
                            color={issueCount > 0 ? 'warning' : 'secondary'}
                            variant="outline"
                            className="w-100"
                            onClick={() => navigate('/admin/flagged-games')}
                        >
                            Flagged Issues{issueCount > 0 ? ` (${issueCount})` : ''}
                        </CButton>
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
