import React, { useState } from 'react'
import {
    CDropdown,
    CDropdownHeader,
    CDropdownMenu,
    CDropdownToggle,
    CFormInput,
    CButton,
    CAlert
} from '@coreui/react'
import {
    cilSettings,
    cilShieldAlt
} from '@coreui/icons'
import CIcon from '@coreui/icons-react'

import { useSelector } from 'react-redux'
import { useNavigate } from 'react-router-dom'

import { loginUser, logoutUser } from 'src/services/authService'

const AppHeaderDropdown = () => {
    const isAdmin = useSelector((state) => state.isAdmin);
    const navigate = useNavigate();
    const [isLoginVisible, setIsLoginVisible] = useState(false);
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState(null);

    const handleLogout = async () => {
        try {
            const request = logoutUser();
            if (request) {
                setIsLoginVisible(false);
                navigate('/');
            } else {
                throw error;
            }
        } catch (error) {
            console.error("An error has occurred", error);
        }
    }

    const handleLogin = async (e) => {
        e.preventDefault();
        setError(null);

        if (!username || !password) {
            setError(true);
            return;
        }
        const credentials = {
            'username': username,
            'password': password
        }

        try {
            const success = await loginUser(credentials);

            if (success) {
                setUsername('');
                setPassword('');
                setIsLoginVisible(false);
                navigate('/admin/calc_values');
            } else {
                throw error;
            }
        } catch (error) {
            setError("Invalid username or password. Please try again.");
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

                {!isAdmin && !isLoginVisible && (
                    <div className="d-flex justify-content-center">
                        <CButton color="primary" className="w-100" onClick={() => setIsLoginVisible(true)}>
                            <CIcon icon={cilSettings} className='me-2' />
                            Login
                        </CButton>
                    </div>
                )}

                {isLoginVisible && !isAdmin && (
                    <div className="p-2">
                        {error && <CAlert color="danger" className="py-1 text-center">{error}</CAlert>}

                        <CFormInput
                            type="text"
                            placeholder="Username"
                            value={username}
                            onChange={(e) => {
                                setUsername(e.target.value);
                                setError(null);
                            }}
                            invalid={error}
                            className="mb-2 p-2 rounded"
                        />
                        <CFormInput
                            type="password"
                            placeholder="Password"
                            value={password}
                            onChange={(e) => {
                                setPassword(e.target.value);
                                setError(null);
                            }}
                            invalid={error}
                            className="mb-2 p-2 rounded"
                        />
                        <CButton color="success" className="w-100 rounded" onClick={handleLogin}>
                            Login
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
