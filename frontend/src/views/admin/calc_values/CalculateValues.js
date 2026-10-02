import React from "react";
import { useEffect, useRef, useState } from "react";
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
    CInputGroup,
    CAlert,
    CSpinner,
    CPopover,
} from "@coreui/react";
import CIcon from '@coreui/icons-react';
import { cilInfo } from '@coreui/icons';
import api from "src/api";
import { useSelector } from "react-redux";
import { format } from "date-fns";
import { CURRENT_RANKING_YEAR } from "src/utils/rankingYear";

const statusMapping = {
    queued: "Queued",
    in_progress: "In Progress",
    complete: "Complete",
    failed: "Failed",
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


const FailureStatus = ({ task }) => {
    const [isOpen, setIsOpen] = useState(false);
    const triggerRef = useRef(null);
    const popoverRef = useRef(null);

    useEffect(() => {
        if (!isOpen) return undefined;

        const closeOnOutsidePointer = (event) => {
            if (triggerRef.current?.contains(event.target) ||
                popoverRef.current?.contains(event.target)) {
                return;
            }
            setIsOpen(false);
        };

        document.addEventListener('pointerdown', closeOnOutsidePointer, true);
        return () => document.removeEventListener('pointerdown', closeOnOutsidePointer, true);
    }, [isOpen]);

    if (task.status !== 'Failed') return task.status;
    const error = task.error || {};
    const content = (
        <div className="small" style={{ maxWidth: '22rem' }}>
            <div><strong>Type:</strong> {error.type || 'Unknown error'}</div>
            <div className="mt-2"><strong>Why:</strong> {error.message || 'No error details were recorded for this execution.'}</div>
            <div className="mt-2"><strong>Where:</strong> {error.location || 'Unavailable'}</div>
        </div>
    );

    return (
        <span className="d-inline-flex align-items-center gap-1 text-danger">
            Failed
            <CPopover
                ref={popoverRef}
                title="Failure details"
                content={content}
                placement="left"
                visible={isOpen}
                onShow={() => setIsOpen(true)}
                onHide={() => setIsOpen(false)}
            >
                <CButton
                    ref={triggerRef}
                    aria-label={`Show failure details for ${task.process}`}
                    color="danger"
                    size="sm"
                    title="Show failure details"
                    variant="ghost"
                    className="p-1"
                >
                    <CIcon icon={cilInfo} size="sm" />
                </CButton>
            </CPopover>
        </span>
    );
};


const CalculateValues = ({ view = 'ranking' }) => {
    const isZScoreView = view === 'z-score';
    const [ value, setValue ] = useState('1');
    const sport = useSelector((state) => state.sport);
    const gender = useSelector((state) => state.gender);
    const level = useSelector((state) => state.level);
    const [ runningTasks, setRunningTasks ] = useState([]);
    const [ zScoreTasks, setZScoreTasks ] = useState([]);
    const [ historyRefresh, setHistoryRefresh ] = useState(0);
    const [ startingTask, setStartingTask ] = useState(false);
    const [ historyError, setHistoryError ] = useState('');

    useEffect(() => {
        let isMounted = true;
        let timeoutId;

        const loadHistory = async () => {
            try {
                const response = await api.get('/execution-history/');
                if (!isMounted) return;
                const records = Array.isArray(response.data?.algorithm)
                    ? response.data.algorithm
                    : [];
                const zScoreRecords = Array.isArray(response.data?.z_scores)
                    ? response.data.z_scores
                    : [];
                setRunningTasks(records.map((record) => ({
                    taskId: record.task_id,
                    enqueueTime: formatDate(record.queued_at),
                    process: 'Main Algorithm Run',
                    runs: record.iterations,
                    startTime: formatDate(record.started_at),
                    finishTime: formatDate(record.finished_at),
                    status: statusMapping[record.status] || 'Unknown',
                    error: record.error,
                })));
                setZScoreTasks(zScoreRecords.map((record) => ({
                    taskId: record.task_id,
                    enqueueTime: formatDate(record.queued_at),
                    process: 'Calculate z Scores',
                    startTime: formatDate(record.started_at),
                    finishTime: formatDate(record.finished_at),
                    status: statusMapping[record.status] || 'Unknown',
                    error: record.error,
                })));
                setHistoryError('');
                const activeRecords = isZScoreView ? zScoreRecords : records;
                if (activeRecords.some((record) =>
                    ['queued', 'in_progress'].includes(record.status))) {
                    timeoutId = setTimeout(loadHistory, 3000);
                }
            } catch (error) {
                if (isMounted) setHistoryError('Execution history could not be loaded.');
            }
        };

        loadHistory();
        return () => {
            isMounted = false;
            clearTimeout(timeoutId);
        };
    }, [historyRefresh, isZScoreView]);

    const startTask = async (endpoint) => {
        setStartingTask(true);
        setHistoryError('');
        try {
            await api.post(
                endpoint, {},
                {
                    headers: { "Content-Type": "application/x-www-form-urlencoded" }
                }
            );
            setHistoryRefresh((previous) => previous + 1);
        } catch (error) {
            setHistoryError(error.response?.data?.detail || (isZScoreView
                ? 'Failed to start z-score calculation.'
                : 'Failed to start the algorithm.'));
        } finally {
            setStartingTask(false);
        }
    };

    const handleAlgoRuns = () => startTask(
        `/run_algorithm/${value}/?sport_type=${sport}&gender=${gender}&level=${level}`
    );

    const handleZScoreCalculation = () => startTask(
        `/calc_z_scores/?sport_type=${sport}&gender=${gender}&level=${level}`
    );

    return (
        <div>
            <h1 className="h2 mb-3">
                {isZScoreView ? 'Z-Score' : `${CURRENT_RANKING_YEAR} Ranking`}
            </h1>
            {historyError && <CAlert color="danger" role="alert">{historyError}</CAlert>}
            {!isZScoreView && <>
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
                                onChange={(event) => setValue(event.target.value)}
                                min={1}
                                max={5}
                                style={{ textAlign: "center" }}
                            />
                        </CInputGroup>
                    </CCol>
                    <CCol xs='auto'>
                        <CButton
                            onClick={handleAlgoRuns}
                            color="primary"
                            type="button"
                            className="ms-3"
                            disabled={startingTask || !Number.isInteger(Number(value)) ||
                                Number(value) < 1 || Number(value) > 5}
                        >
                            {startingTask && <CSpinner className="me-2" size="sm" />}
                            Run Algorithm
                        </CButton>
                    </CCol>
                </CForm>
                <CTable captionTop="Last 5 Execution History">
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
                        {runningTasks.map((task) => (
                            <CTableRow key={task.taskId}>
                                <CTableDataCell>{task.enqueueTime}</CTableDataCell>
                                <CTableDataCell>{task.process}</CTableDataCell>
                                <CTableDataCell>{task.runs}</CTableDataCell>
                                <CTableDataCell>{task.startTime}</CTableDataCell>
                                <CTableDataCell>{task.finishTime}</CTableDataCell>
                                <CTableDataCell><FailureStatus task={task} /></CTableDataCell>
                            </CTableRow>
                        ))}
                    </CTableBody>
                </CTable>
            </>}
            {isZScoreView && <>
                <CButton
                    onClick={handleZScoreCalculation}
                    color="primary"
                    type="button"
                    disabled={startingTask}
                >
                    {startingTask && <CSpinner className="me-2" size="sm" />}
                    Calculate z Scores
                </CButton>
                <CTable captionTop="Last 5 z-Score Execution History" className="mt-3">
                    <CTableHead>
                        <CTableRow>
                            <CTableHeaderCell scope="col">Enqueue Time</CTableHeaderCell>
                            <CTableHeaderCell scope="col">Process</CTableHeaderCell>
                            <CTableHeaderCell scope="col">Start Time</CTableHeaderCell>
                            <CTableHeaderCell scope="col">Finish Time</CTableHeaderCell>
                            <CTableHeaderCell scope="col">Status</CTableHeaderCell>
                        </CTableRow>
                    </CTableHead>
                    <CTableBody>
                        {zScoreTasks.map((task) => (
                            <CTableRow key={task.taskId}>
                                <CTableDataCell>{task.enqueueTime}</CTableDataCell>
                                <CTableDataCell>{task.process}</CTableDataCell>
                                <CTableDataCell>{task.startTime}</CTableDataCell>
                                <CTableDataCell>{task.finishTime}</CTableDataCell>
                                <CTableDataCell><FailureStatus task={task} /></CTableDataCell>
                            </CTableRow>
                        ))}
                    </CTableBody>
                    </CTable>
                </>}
        </div>
    )
}

export default CalculateValues
