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
import { useSelector } from "react-redux";

const CalculateValues = () => {
    const [ value, setValue ] = useState([]);
    const sport = useSelector((state) => state.sport);
    const gender = useSelector((state) => state.gender);
    const level = useSelector((state) => state.level);
    const [ runningTasks, setRunningTasks ] = useState([]);
    const date = new Date();

    const checkTaskStatus = async (taskId) => {
        try {
            const response = await api.get(
                `/task-status/${taskId}`,
                {
                    headers: { "Content-Type": "application/x-www-form-urlencoded" },
                    withCredentials: true,
                }
            );
            return response.data.status; // Example: "PENDING", "RUNNING", "SUCCESS", "FAILED"
        } catch (error) {
            console.error("Error fetching task status:", error);
            return "UNKNOWN";
        }
    };

    const pollTaskStatus = async (taskId) => {
        let status = "PENDING";
        while (status === "PENDING" || status === "STARTED") {  // Need to Change the checks here
            status = await checkTaskStatus(taskId);

            setRunningTasks((prevTasks) =>
                prevTasks.map((task) =>
                    task.taskId === taskId ? { ...task, status } : task
                )
            );

            if (status !== "PENDING" && status !== "STARTED") break;
            await new Promise((resolve) => setTimeout(resolve, 3000));
        }
    };

    const startTask = async (process, endpoint) => {
        // checkAdmin();
        const response = await api.post(
            endpoint,
            {},
            {
                headers: { "Content-Type": "application/x-www-form-urlencoded" },
                withCredentials: true,
            }
        )
        const taskId = response.data.task_id;
        const newTask = {
            dateTime: date.getMonth() + 1 + '/' + date.getDate() + '/' + date.getFullYear(),
            process: process,
            runs: value || 1,
            status: 'PENDING',
            taskId
        }

        setRunningTasks((prev) => [newTask, ...prev]);
        pollTaskStatus(taskId);
    }

    const handleAlgoRuns = () => startTask(
        'Main Algorithm Run',
        `/run_algorithm/${value}/?sport_type=${sport}&gender=${gender}&level=${level}`
    )

    const handleZScores = () => {}

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
                    <CButton onClick={handleAlgoRuns} color="primary" type="button" className="ms-3">
                        Run Alogorithm
                    </CButton>
                </CCol>
                <CCol xs='auto'>
                    <CButton onClick={handleZScores} color="primary" type="button" className="ms-5">
                        Calculate z Scores
                    </CButton>
                </CCol>
            </CForm>
            <CTable captionTop="History">
                <CTableHead>
                    <CTableRow>
                        <CTableHeaderCell scope="col">Date/Time</CTableHeaderCell>
                        <CTableHeaderCell scope="col">Process</CTableHeaderCell>
                        <CTableHeaderCell scope="col">Runs</CTableHeaderCell>
                        <CTableHeaderCell scope="col">Status</CTableHeaderCell>
                    </CTableRow>
                </CTableHead>
                <CTableBody>
                    {runningTasks.map((task, index) => (
                        <CTableRow key={index}>
                            <CTableDataCell>{task.dateTime}</CTableDataCell>
                            <CTableDataCell>{task.process}</CTableDataCell>
                            <CTableDataCell>{task.runs}</CTableDataCell>
                            <CTableDataCell>{task.status}</CTableDataCell>
                        </CTableRow>
                    ))}
                </CTableBody>
            </CTable>
        </div>
    )
}

export default CalculateValues