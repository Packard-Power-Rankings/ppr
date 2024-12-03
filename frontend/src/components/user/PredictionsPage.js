// src/components/user/PredictionsPage.js
import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

const PredictionsPage = () => {
    const { teamOne, teamTwo, homeFieldAdv } = useParams();
    const [predictions, setPredictions] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (!teamOne || !teamTwo) {
            setError('Please select two teams for predictions.');
            setLoading(false);
            return;
        }

        const fetchPredictions = async () => {
            try {
                setLoading(true);
                const response = await fetch(
                    `http://localhost:8000/predictions/${teamOne}/${teamTwo}/${homeFieldAdv}/?gender=mens&level=college`
                );
                if (!response.ok) {
                    throw new Error(`Error: ${response.statusText}`);
                }
                const data = await response.json();
                setPredictions(data);
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };

        fetchPredictions();
    }, [teamOne, teamTwo, homeFieldAdv]);

    if (loading) return <p>Loading predictions...</p>;
    if (error) return <p>Error: {error}</p>;

    return (
        <div>
            <h1>Predictions for {teamOne} vs {teamTwo}</h1>
            <h2>Home Field Advantage: {homeFieldAdv === "true" ? "Yes" : "No"}</h2>
            <pre>{JSON.stringify(predictions, null, 2)}</pre>
        </div>
    );
};

export default PredictionsPage;
