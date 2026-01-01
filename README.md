# SUMO Traffic Simulation - Smart City IoT Demo

Real-world traffic simulation with realistic driver behaviors, Moroccan license plates, and speed radar enforcement, visualized through a modern Web Dashboard.

## Features

- 🚗 **Realistic Driver Profiles** - 5 types from cautious to reckless with randomized parameters
- 🚨 **Speed Radar System** - Configurable radar sensors with violation logging
- 🇲🇦 **Moroccan License Plates** - Authentic format (NNNNN-L-NN)
- 📊 **Web Dashboard** - Real-time visualization of violations and simulation status
- 📝 **Violation Logging** - Detailed speed ticket records stored in PostgreSQL
- 🐳 **Dockerized Stack** - Easy deployment with Docker Compose

## Architecture

The project consists of four main components:

1.  **Frontend (Port 3000)**: React application served via Nginx with Tailwind CSS for visualizing data.
2.  **Backend (Port 5000)**: Flask API managing simulations and serving violation data.
3.  **Database (Port 5433)**: PostgreSQL database storing violation records and simulation logs.
4.  **Simulation**: Headless SUMO simulation running in a Docker container, controlled via the API.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

## Quick Start

1.  **Clone the repository**
2.  **Start the application**
    ```bash
    docker-compose up --build
    ```
3.  **Access the Dashboard**
    Open [http://localhost:3000](http://localhost:3000) in your browser.

## API Documentation

The Backend API runs on `http://localhost:5000`.

### Violations
-   `GET /api/violations`: Retrieve list of speed violations.
    -   Query Params: `simulation_id` (optional)
-   `POST /api/violations`: Record a new violation (used by simulation).

### Simulations
-   `GET /api/simulations`: Get history of all simulations.
-   `POST /api/control/spawn-simulation`: Start a new SUMO simulation instance.
-   `POST /api/simulation/start`: Mark a simulation as running.
-   `POST /api/simulation/end`: Mark a simulation as completed.

### Drivers
-   `GET /api/driver/<plate>`: Get violation history for a specific license plate.

## Project Structure

```
SumoProject/
├── frontend/               # React Web Dashboard (served via Nginx)
├── backend/                # Flask API & Database Logic
├── report/                 # Project documentation & LaTeX report
├── ENSAM_MAP/              # SUMO network & config files
├── sensorsScripts/         # Additional sensor logic
├── docker-compose.yml      # Container orchestration
├── simulation.py           # Main simulation loop
├── driversManagement.py    # Driver behaviors & license plates
├── speedRadar.py           # Radar detection system
├── radars_config.json      # Radar positions & limits
└── test_simulation.sh      # Legacy local test script
```

## Configuration

### Speed Radars
Edit `radars_config.json` to configure detection points:
-   `x`, `y`: Coordinates on the SUMO map
-   `speed_limit`: Speed limit in m/s (4 m/s ≈ 14 km/h)
-   `radius`: Detection range in meters

### Simulation Parameters
-   **Driver Behaviors**: Defined in `driversManagement.py`
-   **Traffic Flow**: Configured in `simulation.py` and `ENSAM_MAP/` files.

## Legacy Mode (Local Run)

If you have SUMO installed locally and want to run the simulation without the full web stack:

```bash
# Run simulation script directly
python simulation.py
```
*Note: This requires SUMO environment variables to be set.*
