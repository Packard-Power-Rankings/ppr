import React, { useCallback } from "react";
import { useDispatch, useSelector } from "react-redux";
import { 
    CCol,
    CButtonGroup,
    CFormCheck,
    CRow,
    CButton
} from "@coreui/react";
import api from "src/api";


const RadioButtonGroup = ({ name, options, selectedValue, onChange }) => {
    return (
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
    );
};

const AdminHeader = () => {
    const dispatch = useDispatch();
    const sport = useSelector(state => state.sport);
    const gender = useSelector(state => state.gender);
    const level = useSelector(state => state.level);

    const updateAdminState = useCallback((key, value) => {
        dispatch({
            type: 'updateAdminState',
            payload: { [key]: value },
        });
    }, [dispatch]);

    const handleClearSeason = async () => {
        try {
            const response = await api.delete(
                `/clear-season/?sport_type=${sport}&gender=${gender}&level=${level}`,
                {
                    headers: {'Content-Type': 'application/json'},
                    withCredentials: true
                }
            );
            console.log(response);
        } catch (error) {
            console.log("Error trying to clear season", error);
        }
    };

    return (
        <CRow className="px-3 pb-2">
            <CCol>
                <RadioButtonGroup
                    name="sportradio"
                    selectedValue={sport}
                    onChange={(value) => updateAdminState('sport', value)}
                    options={[
                        { id: "football", label: "Football", value: "football" },
                        { id: "basketball", label: "Basketball", value: "basketball" }
                    ]}
                />
            </CCol>
            <CCol>
                <RadioButtonGroup
                    name="genderradio"
                    selectedValue={gender}
                    onChange={(value) => updateAdminState('gender', value)}
                    options={[
                        { id: "mens", label: "Mens", value: "mens" },
                        { id: "womens", label: "Womens", value: "womens", disabled: sport === 'football' }
                    ]}
                />
            </CCol>
            <CCol>
                <RadioButtonGroup
                    name="levelradio"
                    selectedValue={level}
                    onChange={(value) => updateAdminState('level', value)}
                    options={[
                        { id: "high_school", label: "High School", value: "high_school" },
                        { id: "college", label: "College", value: "college" }
                    ]}
                />
            </CCol>
            <CCol>
                <CButton as="input" type="button" color="danger" value="Clear Season" onClick={handleClearSeason} />
            </CCol>
        </CRow>
    );
};

export default AdminHeader