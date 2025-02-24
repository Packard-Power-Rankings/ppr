import React from "react";
import { 
    CTable,
    CTableHead,
    CTableBody,
    CTableHeaderCell,
    CTableDataCell,
    CTableRow,
    CButton,
    CForm,
    CCol,
    CFormLabel,
    CFormInput,
    CInputGroup
} from "@coreui/react";
import { useState } from "react";
import api from "src/api";

const CalculateValues = () => {
    const [ value, setValue ] = useState([]);

    return (
        <div>
            <CForm className="row g-3 align-items-center">
                <CFormLabel htmlFor="iterations-counter" className="mb-1">
                    Enter Number of Iterations For Algorithm Run
                </CFormLabel>
                <CCol xs='auto'>
                    <CInputGroup id="basic-addon3">
                        <CFormInput 
                            type="number" 
                            value={value}
                            id="basic-url"
                            aria-describedby="basic-addon3"
                            onChange={(e) => {
                                const newValue = Number(e.target.value);
                                if (newValue > 0 && newValue <= 5) {
                                    setValue(newValue);
                                }
                            }} 
                            style={{ textAlign: "center" }} 
                        />
                    </CInputGroup>
                </CCol>
                <CCol xs='auto'>
                    <CButton color="primary" type="submit" className="ms-3">
                        Run Alogorithm
                    </CButton>
                </CCol>
                <CCol xs='auto'>
                    <CButton color="primary" type="submit" className="ms-5">
                        Calculate z Scores
                    </CButton>
                </CCol>
            </CForm>
            <CTable captionTop="History">
                <CTableHead>
                    <CTableRow>
                        <CTableHeaderCell scope="col">Date/Time</CTableHeaderCell>
                        <CTableHeaderCell scope="col">Runs</CTableHeaderCell>
                        <CTableHeaderCell scope="col">Status</CTableHeaderCell>
                    </CTableRow>
                </CTableHead>
            </CTable>
        </div>
    )
}

export default CalculateValues