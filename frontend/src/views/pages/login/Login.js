import React, { useState } from 'react'
import { useSelector } from 'react-redux'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import {
    CButton,
    CCard,
    CCardBody,
    CCol,
    CContainer,
    CForm,
    CFormInput,
    CInputGroup,
    CInputGroupText,
    CRow,
    CSpinner,
} from '@coreui/react'
import CIcon from '@coreui/icons-react'
import { cilLockLocked, cilUser } from '@coreui/icons'
import { loginUser } from 'src/services/authService'

const Login = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [errorMessage, setErrorMessage] = useState('');
    const [error, setError] = useState(false);

    const authReady = useSelector((state) => state.authReady);
    const isAdmin = useSelector((state) => state.isAdmin);
    const location = useLocation();
    const navigate = useNavigate();
    const previousLocation = location.state?.from;
    const returnTo = previousLocation
        ? `${previousLocation.pathname}${previousLocation.search}${previousLocation.hash}`
        : '/admin';

    const handleSubmit = async (e) => {
        e.preventDefault();
        setErrorMessage('');
        setError(false);

        if (!username || !password) {
            setErrorMessage("Please Enter User Name and Password");
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
                navigate(returnTo, { replace: true });
            } else {
                setErrorMessage("Invalid username or password");
                setError(true);
            }
        } catch (error) {
            console.error("Failed to sign in", error);
            setErrorMessage("Unable to sign in. Please try again.");
            setError(true);
        }
    };

    if (!authReady) {
        return (
            <div className="bg-body-tertiary min-vh-100 d-flex align-items-center justify-content-center">
                <CSpinner color="primary" />
            </div>
        );
    }

    if (isAdmin) {
        return <Navigate to="/admin" replace />;
    }

    return (
        <div className="bg-body-tertiary min-vh-100 d-flex flex-row align-items-center">
            <CContainer>
                <CRow className="justify-content-center">
                    <CCol md={5}>
                        <CCard className="p-4">
                            <CCardBody>
                                <CForm onSubmit={handleSubmit}>
                                    <h1>Admin Login</h1>
                                    <p className="text-body-secondary">Sign in to manage rankings data.</p>
                                    {errorMessage && <p className="text-danger text-center">{errorMessage}</p>}
                                    <CInputGroup className="mb-3">
                                        <CInputGroupText>
                                            <CIcon icon={cilUser} />
                                        </CInputGroupText>
                                        <CFormInput
                                            placeholder="Username"
                                            autoComplete="username"
                                            onChange={(e) => setUsername(e.target.value)}
                                            invalid={error}
                                        />
                                    </CInputGroup>
                                    <CInputGroup className="mb-4">
                                        <CInputGroupText>
                                            <CIcon icon={cilLockLocked} />
                                        </CInputGroupText>
                                        <CFormInput
                                            type={showPassword ? 'text' : 'password'}
                                            placeholder="Password"
                                            autoComplete="current-password"
                                            onChange={(e) => setPassword(e.target.value)}
                                            invalid={error}
                                        />
                                    </CInputGroup>
                                    <div className="form-check mb-4">
                                        <input
                                            className="form-check-input"
                                            id="show-password"
                                            type="checkbox"
                                            checked={showPassword}
                                            onChange={(e) => setShowPassword(e.target.checked)}
                                        />
                                        <label className="form-check-label" htmlFor="show-password">
                                            Show password
                                        </label>
                                    </div>
                                    <CRow className="g-2">
                                        <CCol xs={12}>
                                            <CButton type="submit" color="primary" className="w-100">
                                                Login
                                            </CButton>
                                        </CCol>
                                        <CCol xs={12} className="text-center">
                                            <CButton color="link" onClick={() => navigate('/')}>
                                                Return to public site
                                            </CButton>
                                        </CCol>
                                    </CRow>
                                </CForm>
                            </CCardBody>
                        </CCard>
                    </CCol>
                </CRow>
            </CContainer>
        </div>
    );
};

export default Login;
