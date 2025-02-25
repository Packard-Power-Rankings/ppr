import React, { useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { 
    CCol,
    CButtonGroup,
    CFormCheck,
    CRow
} from "@coreui/react";


const AdminHeader = () => {
    const dispatch = useDispatch();
    const sport = useSelector((state) => state.sport);
    const gender = useSelector((state) => state.gender);
    const level = useSelector((state) => state.level);

    const updateAdminState = (key, value) => {
        dispatch({
            type: 'updateAdminState',
            payload: {[key]: value},
        })
    }

    return (
        <div>
            <CRow>
                <CCol>
                    <CButtonGroup vertical role="group" aria-label="Vertical button group">
                        <CFormCheck 
                            type="radio"
                            name="sportradio"
                            id="football"
                            autoComplete="off"
                            label='Football'
                            onChange={() => updateAdminState('sport', 'football')}
                            checked={sport === 'football'}
                        />
                        <CFormCheck 
                            type="radio"
                            name="sportradio"
                            id="basketball"
                            autoComplete="off"
                            label='Basketball'
                            onChange={() => updateAdminState('sport', 'basketball')}
                            checked={sport === 'basketball'}
                        />
                    </CButtonGroup>
                </CCol>
                <CCol>
                    <CButtonGroup vertical role="group" aria-label="Vertical button group">
                        <CFormCheck 
                            type="radio"
                            name="genderradio"
                            id="mens"
                            autoComplete="off"
                            label='Mens'
                            onChange={() => updateAdminState('gender', 'mens')}
                            checked={gender === 'mens'}
                        />
                        <CFormCheck 
                            type="radio"
                            name="genderradio"
                            id="womens"
                            autoComplete="off"
                            label='Womens'
                            onChange={() => updateAdminState('gender','womens')}
                            checked={gender === 'womens'}
                            disabled={sport === 'football'}
                        />
                    </CButtonGroup>
                </CCol>
                <CCol>
                    <CButtonGroup vertical role="group" aria-label="Vertical button group">
                        <CFormCheck 
                            type="radio"
                            name="levelradio"
                            id="high_school"
                            autoComplete="off"
                            label='High School'
                            onChange={() => updateAdminState('level', 'high_school')}
                            checked={level === 'high_school'}
                        />
                        <CFormCheck 
                            type="radio"
                            name="levelradio"
                            id="college"
                            autoComplete="off"
                            label='College'
                            onChange={() => updateAdminState('level','college')}
                            checked={level === 'college'}
                        />
                    </CButtonGroup>
                </CCol>
            </CRow>
        </div>
    )
}

export default AdminHeader