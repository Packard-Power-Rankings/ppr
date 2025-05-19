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
import { format } from "date-fns";

const statusMapping = {
    queued: "Queued",
    in_progress: "In Progress",
    complete: "Complete",
    deferred: "Deferred",
    not_found: "Not Found",
};


const formatDate = (dateString) => {
    if (!dateString || dateString === "N/A") return "N/A";
    try {
        return format(new Date(dateString), "MM-dd-yyyy hh:mm:ss bbb");
    } catch (error) {
        return "Invalid Date";
    }
};


const CalculateValues = () => {
    const [ value, setValue ] = useState([]);
    const sport = useSelector((state) => state.sport);
    const gender = useSelector((state) => state.gender);
    const level = useSelector((state) => state.level);
    const [ runningTasks, setRunningTasks ] = useState([]);
    // const date = new Date();

    const checkTaskStatus = async (taskId) => {
        try {
            const response = await api.get(
                `/task-status/${taskId}`,
                {
                    headers: { "Content-Type": "application/x-www-form-urlencoded" },
                    withCredentials: true,
                }
            );
            return response.data;
        } catch (error) {
            console.error("Error fetching task status:", error);
            return "UNKNOWN";
        }
    };

    const pollTaskStatus = async (taskId, process, runs) => {
        let taskStatus = await checkTaskStatus(taskId);
        setRunningTasks((prev) => [
            { taskId, process, runs, status: statusMapping[taskStatus.status] || "Unknown", startTime: taskStatus.info?.start_time || "N/A" },
            ...prev,
        ]);

        while (taskStatus.status === "queued" || taskStatus.status === "in_progress") {
            await new Promise((resolve) => setTimeout(resolve, 3000));
            taskStatus = await checkTaskStatus(taskId);

            setRunningTasks((prev) =>
                prev.map((task) =>
                    task.taskId === taskId
                        ? {
                              ...task,
                              status: statusMapping[taskStatus.status] || "Unknown",
                              enqueueTime: formatDate(taskStatus.info?.enqueue_time),
                              startTime: formatDate(taskStatus.info?.start_time),
                              finishTime: formatDate(taskStatus.info?.finish_time),
                              success: taskStatus.info?.success !== undefined ? (taskStatus.info.success ? "Success" : "Failed") : "Pending",
                          }
                        : task
                )
            );

            if (taskStatus.status === "complete") break;
        }
    };

    const startTask = async (process, endpoint) => {
        const response = await api.post(
            endpoint, {},
            {
                headers: { "Content-Type": "application/x-www-form-urlencoded" },
                withCredentials: true
            }
        );
        const taskId = response.data.task_id;
        pollTaskStatus(taskId, process, value || 1);
    };

    const handleAlgoRuns = () => startTask(
        'Main Algorithm Run',
        `/run_algorithm/${value}/?sport_type=${sport}&gender=${gender}&level=${level}`
    )

    const handleZScores = () => startTask(
        'Calculating z-Scores',
        `/calc_z_scores/?sport_type=${sport}&gender=${gender}&level=${level}`
    )

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
                        <CTableHeaderCell scope="col">Enqueue Time</CTableHeaderCell>
                        <CTableHeaderCell scope="col">Process</CTableHeaderCell>
                        <CTableHeaderCell scope="col">Runs</CTableHeaderCell>
                        <CTableHeaderCell scope="col">Start Time</CTableHeaderCell>
                        <CTableHeaderCell scope="col">Finish Time</CTableHeaderCell>
                        <CTableHeaderCell scope="col">Status</CTableHeaderCell>
                    </CTableRow>
                </CTableHead>
                <CTableBody>
                    {runningTasks.map((task, index) => (
                        <CTableRow key={index}>
                            <CTableDataCell>{task.enqueueTime}</CTableDataCell>
                            <CTableDataCell>{task.process}</CTableDataCell>
                            <CTableDataCell>{task.runs}</CTableDataCell>
                            <CTableDataCell>{task.startTime}</CTableDataCell>
                            <CTableDataCell>{task.finishTime}</CTableDataCell>
                            <CTableDataCell>{task.status}</CTableDataCell>
                        </CTableRow>
                    ))}
                </CTableBody>
            </CTable>
        </div>
    )
}

export default CalculateValues