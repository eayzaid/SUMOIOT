import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import '../App.css';
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
    AlertDialogTrigger,
} from "./ui/alert-dialog"
import { Button } from "./ui/button"

function Dashboard() {
    const navigate = useNavigate();
    const [violations, setViolations] = useState([]);
    const [simulations, setSimulations] = useState([]);
    const [selectedSimulation, setSelectedSimulation] = useState('');
    const [selectedDriver, setSelectedDriver] = useState(null);
    const [driverHistory, setDriverHistory] = useState([]);
    const [currentSimStatus, setCurrentSimStatus] = useState(null);
    const [elapsedTime, setElapsedTime] = useState(0);
    const [loading, setLoading] = useState(true);
    const [starting, setStarting] = useState(false);
    const [error, setError] = useState(null);
    const [currentPage, setCurrentPage] = useState(1);
    const itemsPerPage = 10;

    const API_BASE = 'http://localhost:5000/api';

    const fetchSimulations = async () => {
        try {
            const response = await fetch(`${API_BASE}/simulations`);
            if (response.ok) {
                const data = await response.json();
                setSimulations(data);

                // Auto-select latest if none selected
                if (!selectedSimulation && data.length > 0) {
                    setSelectedSimulation(data[0].simulation_id);
                }

                // Update current simulation status info
                if (selectedSimulation) {
                    const sim = data.find(s => s.simulation_id === selectedSimulation);
                    if (sim) {
                        setCurrentSimStatus(sim);
                    }
                } else if (data.length > 0) {
                    setCurrentSimStatus(data[0]);
                }
            }
        } catch (err) {
            console.error("Error fetching simulations:", err);
        }
    };

    const fetchViolations = async () => {
        try {
            let url = `${API_BASE}/violations`;
            if (selectedSimulation) {
                url += `?simulation_id=${selectedSimulation}`;
            }

            const response = await fetch(url);
            if (!response.ok) {
                throw new Error('Failed to fetch violations');
            }
            const data = await response.json();
            setViolations(data);
            setLoading(false);
        } catch (err) {
            console.error("Error fetching violations:", err);
            setError(err.message);
            setLoading(false);
        }
    };

    const fetchDriverHistory = async (plate) => {
        try {
            const response = await fetch(`${API_BASE}/driver/${plate}`);
            if (response.ok) {
                const data = await response.json();
                setDriverHistory(data);
                setSelectedDriver(plate);
            }
        } catch (err) {
            console.error("Error fetching driver history:", err);
        }
    };

    const startNewSimulation = async () => {


        setStarting(true);
        try {
            const response = await fetch(`${API_BASE}/control/spawn-simulation`, { method: 'POST' });
            if (!response.ok) throw new Error('Failed to start simulation');

            // Wait a bit for container to start
            setTimeout(() => {
                setStarting(false);
                window.location.reload(); // Reload to get fresh state
            }, 2000);
        } catch (err) {
            console.error("Error starting simulation:", err);
            alert("Failed to start simulation: " + err.message);
            setStarting(false);
        }
    };

    useEffect(() => {
        fetchSimulations();
        const interval = setInterval(() => {
            fetchSimulations();
            fetchViolations();
        }, 2000);
        return () => clearInterval(interval);
    }, [selectedSimulation]);

    // Update timer
    useEffect(() => {
        const timer = setInterval(() => {
            if (currentSimStatus) {
                const start = new Date(currentSimStatus.start_time).getTime();
                const end = currentSimStatus.end_time ? new Date(currentSimStatus.end_time).getTime() : Date.now();
                setElapsedTime(Math.floor((end - start) / 1000));
            }
        }, 1000);
        return () => clearInterval(timer);
    }, [currentSimStatus]);

    // Initial fetch when simulation changes
    useEffect(() => {
        if (selectedSimulation) {
            fetchViolations();
            // Update status immediately
            const sim = simulations.find(s => s.simulation_id === selectedSimulation);
            if (sim) setCurrentSimStatus(sim);
        }
    }, [selectedSimulation, simulations]);

    const formatDuration = (seconds) => {
        const m = Math.floor(seconds / 60);
        const s = seconds % 60;
        return `${m}m ${s}s`;
    };

    // Pagination logic
    const indexOfLastItem = currentPage * itemsPerPage;
    const indexOfFirstItem = indexOfLastItem - itemsPerPage;
    const currentViolations = violations.slice(indexOfFirstItem, indexOfLastItem);
    const totalPages = Math.ceil(violations.length / itemsPerPage);

    const handleNextPage = () => {
        if (currentPage < totalPages) setCurrentPage(currentPage + 1);
    };

    const handlePrevPage = () => {
        if (currentPage > 1) setCurrentPage(currentPage - 1);
    };

    // Reset page when simulation changes
    useEffect(() => {
        setCurrentPage(1);
    }, [selectedSimulation]);

    const handleLogout = () => {
        localStorage.removeItem('isAuthenticated');
        navigate('/login');
    };

    return (
        <div className="App">
            <header className="App-header">
                <h1>SUMO Speed Violations</h1>
                <div className="simulation-selector">
                    <label>Simulation Run: </label>
                    <select
                        value={selectedSimulation}
                        onChange={(e) => setSelectedSimulation(e.target.value)}
                    >
                        <option value="">All Simulations</option>
                        {simulations.map(sim => (
                            <option key={sim.simulation_id} value={sim.simulation_id}>
                                {new Date(sim.start_time).toLocaleString()} ({sim.violation_count} violations)
                            </option>
                        ))}
                    </select>
                </div>

                {currentSimStatus && (
                    <div className="simulation-status-bar">
                        <div className={`status-badge ${currentSimStatus.status === 'RUNNING' ? 'running' : 'completed'}`}>
                            {currentSimStatus.status === 'RUNNING' ? 'ONGOING' : 'FINISHED'}
                        </div>
                        <div className="duration-display">
                            Duration: {formatDuration(elapsedTime)}
                        </div>
                    </div>
                )}

                <AlertDialog>
                    <AlertDialogTrigger asChild>
                        <Button
                            className="restart-button"
                            disabled={starting}
                        >
                            {starting ? 'Starting...' : 'Start New Simulation'}
                        </Button>
                    </AlertDialogTrigger>
                    <AlertDialogContent>
                        <AlertDialogHeader>
                            <AlertDialogTitle>Start New Simulation?</AlertDialogTitle>
                            <AlertDialogDescription>
                                This will start a new Simulation.
                            </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                            <AlertDialogCancel>Cancel</AlertDialogCancel>
                            <AlertDialogAction onClick={startNewSimulation}>Continue</AlertDialogAction>
                        </AlertDialogFooter>
                    </AlertDialogContent>
                </AlertDialog>
                <button className="logout-button" onClick={handleLogout}>
                    Logout
                </button>
            </header>

            <main className="container">
                {error && <div className="error-message">Error: {error}</div>}

                {selectedDriver ? (
                    <div className="driver-details-view">
                        <button className="back-button" onClick={() => setSelectedDriver(null)}>← Back to Dashboard</button>
                        <h2>Driver History: <span className="plate-large">{selectedDriver}</span></h2>
                        <div className="stats-panel">
                            <div className="stat-card">
                                <h3>Total Offenses</h3>
                                <p className="stat-value">{driverHistory.length}</p>
                            </div>
                            <div className="stat-card">
                                <h3>Max Speed</h3>
                                <p className="stat-value">
                                    {Math.max(...driverHistory.map(v => v.actual_speed_kmh)).toFixed(1)} km/h
                                </p>
                            </div>
                        </div>
                        <div className="violations-list">
                            <table>
                                <thead>
                                    <tr>
                                        <th>Time</th>
                                        <th>Radar</th>
                                        <th>Location</th>
                                        <th>Speed (km/h)</th>
                                        <th>Limit</th>
                                        <th>Overspeed</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {driverHistory.map((v) => (
                                        <tr key={v.id}>
                                            <td>{new Date(v.created_at).toLocaleTimeString()}</td>
                                            <td>{v.radar_id}</td>
                                            <td>{v.description} <br /><small>(X: {v.location_x.toFixed(0)}, Y: {v.location_y.toFixed(0)})</small></td>
                                            <td className="speed-high">{v.actual_speed_kmh.toFixed(1)}</td>
                                            <td>{v.speed_limit_kmh.toFixed(0)}</td>
                                            <td className="overspeed">+{v.overspeed_kmh.toFixed(1)}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                ) : (
                    <>
                        <div className="stats-panel">
                            <div className="stat-card">
                                <h3>Violations (Current View)</h3>
                                <p className="stat-value">{violations.length}</p>
                            </div>
                            <div className="stat-card">
                                <h3>Latest Violation</h3>
                                <p className="stat-value">
                                    {violations.length > 0 ? `${violations[0].actual_speed_kmh.toFixed(1)} km/h` : '-'}
                                </p>
                            </div>
                        </div>

                        <div className="violations-list">
                            <h2>Recent Violations</h2>
                            {violations.length === 0 ? (
                                <p>No violations detected yet.</p>
                            ) : (
                                <table>
                                    <thead>
                                        <tr>
                                            <th>Time</th>
                                            <th>Radar</th>
                                            <th>Location</th>
                                            <th>Vehicle</th>
                                            <th>Plate</th>
                                            <th>Speed (km/h)</th>
                                            <th>Limit</th>
                                            <th>Overspeed</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {currentViolations.map((v) => (
                                            <tr key={v.id} className="violation-row">
                                                <td>{new Date(v.created_at).toLocaleTimeString()}</td>
                                                <td>{v.radar_id}</td>
                                                <td>
                                                    {v.description}
                                                    <div className="location-coords">X: {v.location_x.toFixed(0)}, Y: {v.location_y.toFixed(0)}</div>
                                                </td>
                                                <td>{v.vehicle_id}</td>
                                                <td>
                                                    <span
                                                        className="plate clickable"
                                                        onClick={() => fetchDriverHistory(v.license_plate)}
                                                        title="View Driver History"
                                                    >
                                                        {v.license_plate}
                                                    </span>
                                                </td>
                                                <td className="speed-high">{v.actual_speed_kmh.toFixed(1)}</td>
                                                <td>{v.speed_limit_kmh.toFixed(0)}</td>
                                                <td className="overspeed">+{v.overspeed_kmh.toFixed(1)}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            )}

                            {violations.length > 0 && (
                                <div className="pagination-controls flex justify-center items-center gap-4 mt-4">
                                    <Button
                                        variant="outline"
                                        onClick={handlePrevPage}
                                        disabled={currentPage === 1}
                                    >
                                        Previous
                                    </Button>
                                    <span className="text-sm">
                                        Page {currentPage} of {totalPages}
                                    </span>
                                    <Button
                                        variant="outline"
                                        onClick={handleNextPage}
                                        disabled={currentPage === totalPages}
                                    >
                                        Next
                                    </Button>
                                </div>
                            )}
                        </div>
                    </>
                )}
            </main>
        </div>
    );
}

export default Dashboard;
