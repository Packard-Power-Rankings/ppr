import React, { useCallback } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { CButtonGroup, CCol, CFormCheck, CRow } from '@coreui/react'

const RadioButtonGroup = ({ name, options, selectedValue, onChange }) => (
  <CButtonGroup vertical role="group" aria-label={`${name} button group`} className="mb-2">
    {options.map(({ id, label, value, disabled }) => (
      <CFormCheck
        key={id}
        type="radio"
        name={name}
        id={id}
        autoComplete="off"
        label={label}
        onChange={() => onChange(value)}
        checked={selectedValue === value}
        disabled={disabled}
        className="me-3"
      />
    ))}
  </CButtonGroup>
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
    <CRow className="px-3 pb-2" aria-label="Admin dataset selection">
      <CCol>
        <RadioButtonGroup
          name="sport"
          selectedValue={sport}
          onChange={updateSport}
          options={[
            { id: 'football', label: 'Football', value: 'football' },
            { id: 'basketball', label: 'Basketball', value: 'basketball' },
          ]}
        />
      </CCol>
      <CCol>
        <RadioButtonGroup
          name="gender"
          selectedValue={gender}
          onChange={(value) => updateAdminState('gender', value)}
          options={[
            { id: 'mens', label: 'Mens', value: 'mens' },
            { id: 'womens', label: 'Womens', value: 'womens', disabled: sport === 'football' },
          ]}
        />
      </CCol>
      <CCol>
        <RadioButtonGroup
          name="level"
          selectedValue={level}
          onChange={(value) => updateAdminState('level', value)}
          options={[
            { id: 'high_school', label: 'High School', value: 'high_school' },
            { id: 'college', label: 'College', value: 'college' },
          ]}
        />
      </CCol>
    </CRow>
  )
}

export default AdminHeader
