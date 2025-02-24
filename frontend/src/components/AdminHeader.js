import React from "react";
import { 
    CCol,
    CButtonGroup,
    CFormCheck,
    CRow
} from "@coreui/react";


const AdminHeader = () => {
    return (
        <div>
            <CRow>
                <CCol>
                    <CButtonGroup vertical role="group" aria-label="Vertical button group">
                        <CFormCheck 
                            type="radio"
                            name="sportradio"
                            id="sportradio1"
                            autoComplete="off"
                            label='Football'
                            defaultChecked
                        />
                        <CFormCheck 
                            type="radio"
                            name="sportradio"
                            id="sportradio1"
                            autoComplete="off"
                            label='Basketball'
                            defaultChecked
                        />
                    </CButtonGroup>
                </CCol>
                <CCol>
                    <CButtonGroup vertical role="group" aria-label="Vertical button group">
                        <CFormCheck 
                            type="radio"
                            name="genderradio"
                            id="genderradio1"
                            autoComplete="off"
                            label='Mens'
                            defaultChecked
                        />
                        <CFormCheck 
                            type="radio"
                            name="genderradio"
                            id="genderradio2"
                            autoComplete="off"
                            label='Womens'
                            defaultChecked
                        />
                    </CButtonGroup>
                </CCol>
                <CCol>
                    <CButtonGroup vertical role="group" aria-label="Vertical button group">
                        <CFormCheck 
                            type="radio"
                            name="levelradio"
                            id="levelradio1"
                            autoComplete="off"
                            label='High School'
                            defaultChecked
                        />
                        <CFormCheck 
                            type="radio"
                            name="levelradio"
                            id="levelradio1"
                            autoComplete="off"
                            label='College'
                            defaultChecked
                        />
                    </CButtonGroup>
                </CCol>
            </CRow>
        </div>
    )
}

export default AdminHeader