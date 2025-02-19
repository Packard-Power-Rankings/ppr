import React from "react";
import {
    CTable,
    CTableHead,
    CTableRow,
    CTableHeaderCell,
    CTableDataCell,
    CTableBody
} from '@coreui/react'

const Teams = () => {
    return (
        <div>
            <CTable>
                <CTableHead>
                    <CTableRow>
                        <CTableHeaderCell scope="col">Rank</CTableHeaderCell>
                        <CTableHeaderCell scope="col">Team</CTableHeaderCell>
                        <CTableHeaderCell scope="col">Power</CTableHeaderCell>
                        <CTableHeaderCell scope="col">Div. Rank</CTableHeaderCell>
                        <CTableHeaderCell scope="col">Div.</CTableHeaderCell>
                        <CTableHeaderCell scope="col">W</CTableHeaderCell>
                        <CTableHeaderCell scope="col">L</CTableHeaderCell>
                    </CTableRow>
                </CTableHead>
            </CTable>
        </div>
    )
}

export default Teams