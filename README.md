# SUMO Traffic Simulation - Smart City IoT Demo

Real-world traffic simulation with realistic driver behaviors, Moroccan license plates, and speed radar enforcement for smart city demonstration.

## Features

- 🚗 **Realistic Driver Profiles** - 5 types from cautious to reckless with randomized parameters
- 🚨 **Speed Radar System** - Configurable radar sensors with violation logging
- 🇲🇦 **Moroccan License Plates** - Authentic format (NNNNN-L-NN)
- 📊 **Driver Behavior Simulation** - Speed variations, random errors, fatigue effects
- 📝 **Violation Logging** - Detailed speed ticket records with timestamps

## Prerequisites

**SUMO Installation Required:**

1. Install SUMO from [https://sumo.dlr.de](https://sumo.dlr.de)
2. Set environment variable: `SUMO_HOME` → path to SUMO installation
3. Add to PATH: `%SUMO_HOME%\bin` and `%SUMO_HOME%\tools`

**Verify installation:**
```bash
sumo --version
python %SUMO_HOME%\tools\randomTrips.py --help
```

## Quick Start

```bash
# Run full test (generates 1000 trips + 3600 step simulation)
./test_simulation.sh

# Or run simulation directly
python simulation.py
```

## Configuration

**Speed Radars:** Edit `radars_config.json`
- Set radar coordinates (x, y)
- Configure speed limits (m/s: 4 m/s ≈ 14 km/h)
- Adjust detection radius (default 80m)

**Trip Generation:** Edit `test_simulation.sh`
- Modify `NUM_TRIPS` for vehicle count
- Adjust `END_TIME` for simulation duration

## Project Structure

```
SumoProject/
├── simulation.py           # Main simulation loop
├── driversManagement.py    # Driver behaviors & license plates
├── speedRadar.py          # Radar detection system
├── radars_config.json     # Radar positions & limits
├── test_simulation.sh     # Automated test script
├── ENSAM_MAP/             # SUMO network & config files
└── speed_violations.log   # Auto-generated violation log
```

## Output

- **Console:** Real-time violation alerts
- **speed_violations.log:** Detailed ticket records
- **ENSAM_MAP/tripinfos.xml:** Vehicle trip statistics
- **ENSAM_MAP/stats.xml:** Simulation summary

## Demo Purpose

IoT smart city presentation demonstrating automated traffic enforcement with realistic driver behavior modeling.
