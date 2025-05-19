import React, { useState } from 'react'
import { useDispatch } from 'react-redux'
import { useNavigate } from 'react-router-dom'
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
} from '@coreui/react'
import CIcon from '@coreui/icons-react'
import { cilLockLocked, cilUser } from '@coreui/icons'
import { loginUser } from 'src/services/authService'

const Login = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [errorMessage, setErrorMessage] = useState('');
    const [error, setError] = useState(false);

    const dispatch = useDispatch();
    const navigate = useNavigate();

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
                dispatch({ type: 'login' });
                navigate('/admin/calc_values')
            } else {
                setErrorMessage("Invalid username or password");
                setError(true);
            }
        } catch (error) {
            console.error("Failed to sign in", error);
        }
    };

    const handleForgotPassword = () => {
        alert("Forgot password functionality not implemented yet.");
    };

    return (
        <div className="bg-body-tertiary min-vh-100 d-flex flex-row align-items-center">
            <CContainer>
                <CRow className="justify-content-center">
                    <CCol md={5}>
                        <CCard className="p-4">
                            <CCardBody>
                                <CForm onSubmit={handleSubmit}>
                                    <h1>Login</h1>
                                    <p className="text-body-secondary">Sign In to your account</p>
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
                                            type="password"
                                            placeholder="Password"
                                            autoComplete="current-password"
                                            onChange={(e) => setPassword(e.target.value)}
                                            invalid={error}
                                        />
                                    </CInputGroup>
                                    <CRow>
                                        <CCol xs={6}>
                                            <CButton type='submit' color="primary" className="px-4">
                                                Login
                                            </CButton>
                                        </CCol>
                                        <CCol xs={6} className="text-right">
                                            <CButton color="link" className="px-0" onClick={handleForgotPassword}>
                                                Forgot password?
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