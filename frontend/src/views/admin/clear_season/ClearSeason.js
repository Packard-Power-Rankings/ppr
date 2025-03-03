import React from "react";
import {
    CButton
} from "@coreui/react";
import api from "src/api";
import { useSelector } from "react-redux";

const ClearSeason = () => {
    const sport = useSelector((state) => state.sport);
    const gender = useSelector((state) => state.gender);
    const level = useSelector((state) => state.level);

    const handleSubmit = async () => {
        try {
            const response = await api.delete(
                `/clear-season/?sport_type=${sport}&gender=${gender}&level=${level}`,
                {
                    headers: {'Content-Type': 'application/json'},
                    withCredentials: true
                }
            )
            console.log(response);
        } catch (error) {
            console.log("Error trying to clear season", error);
        }
    }

    return (
        <>
            <CButton onClick={handleSubmit} as="input" type="submit" color="primary" value="Submit" />
        </>
    )
}

export default ClearSeason