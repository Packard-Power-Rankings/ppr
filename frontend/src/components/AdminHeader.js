import React, { useCallback } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { CCol, CFormLabel, CFormSelect, CRow } from '@coreui/react'

const DatasetSelect = ({ id, label, options, value, onChange }) => (
  <>
    <CFormLabel htmlFor={id}>{label}</CFormLabel>
    <CFormSelect
      id={id}
      value={value}
      onChange={(event) => onChange(event.target.value)}
    >
      {options.map((option) => (
        <option key={option.value} value={option.value} disabled={option.disabled}>
          {option.label}
        </option>
      ))}
    </CFormSelect>
  </>
)

const AdminHeader = () => {
  const dispatch = useDispatch()
  const sport = useSelector((state) => state.sport)
  const gender = useSelector((state) => state.gender)
  const level = useSelector((state) => state.level)

  const updateAdminState = useCallback((key, value) => {
    dispatch({
      type: 'updateAdminState',
      payload: { [key]: value },
    })
  }, [dispatch])

  const updateSport = (value) => {
    dispatch({
      type: 'updateAdminState',
      payload: {
        sport: value,
        ...(value === 'football' && gender === 'womens' ? { gender: 'mens' } : {}),
      },
    })
  }

  return (
    <CRow className="px-3 pb-3 g-3" aria-label="Admin dataset selection">
      <CCol xs={12} md={4}>
        <DatasetSelect
          id="admin-sport"
          label="Sport"
          value={sport}
          onChange={updateSport}
          options={[
            { label: 'Football', value: 'football' },
            { label: 'Basketball', value: 'basketball' },
          ]}
        />
      </CCol>
      <CCol xs={12} md={4}>
        <DatasetSelect
          id="admin-gender"
          label="Gender"
          value={gender}
          onChange={(value) => updateAdminState('gender', value)}
          options={[
            { label: 'Mens', value: 'mens' },
            { label: 'Womens', value: 'womens', disabled: sport === 'football' },
          ]}
        />
      </CCol>
      <CCol xs={12} md={4}>
        <DatasetSelect
          id="admin-level"
          label="Level"
          value={level}
          onChange={(value) => updateAdminState('level', value)}
          options={[
            { label: 'High School', value: 'high_school' },
            { label: 'College', value: 'college' },
          ]}
        />
      </CCol>
    </CRow>
  )
}

export default AdminHeader
