#!/bin/bash

# ============================================================
# SUMO Simulation Test Script
# Generates 1000 random trips and runs simulation for 3600 steps
# ============================================================

echo "=========================================="
echo "SUMO Simulation Test Script"
echo "=========================================="

# Check if SUMO_HOME is set
if [ -z "$SUMO_HOME" ]; then
    echo "ERROR: SUMO_HOME environment variable is not set!"
    echo "Please set it to your SUMO installation directory."
    exit 1
fi

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MAP_DIR="$PROJECT_DIR/ENSAM_MAP"
NETWORK_FILE="$MAP_DIR/osm.net.xml.gz"
TRIPS_FILE="$MAP_DIR/trips.trips.xml"
ROUTES_FILE="$MAP_DIR/routes.rou.xml"
CONFIG_FILE="$MAP_DIR/config.sumocfg"

# Trip generation parameters
NUM_TRIPS=1000
BEGIN_TIME=0
END_TIME=3600
TRIP_ATTRIBUTES="departLane=\"best\" departSpeed=\"max\""

echo ""
echo "Configuration:"
echo "  Network: $NETWORK_FILE"
echo "  Trips: $NUM_TRIPS"
echo "  Duration: $END_TIME seconds"
echo "  Output: $TRIPS_FILE"
echo ""

# Step 1: Check if network file exists
echo "[1/3] Checking network file..."
if [ ! -f "$NETWORK_FILE" ]; then
    echo "ERROR: Network file not found: $NETWORK_FILE"
    exit 1
fi
echo "✓ Network file found"
echo ""

# Step 2: Generate random trips
echo "[2/3] Generating $NUM_TRIPS random trips..."
python "$SUMO_HOME/tools/randomTrips.py" \
    -n "$NETWORK_FILE" \
    -o "$TRIPS_FILE" \
    --begin $BEGIN_TIME \
    --end $END_TIME \
    --period $((END_TIME / NUM_TRIPS)) \
    --fringe-factor 5 \
    --trip-attributes "$TRIP_ATTRIBUTES" \
    --validate \
    --verbose

if [ $? -ne 0 ]; then
    echo "ERROR: Trip generation failed!"
    exit 1
fi

# Clean up unwanted route file (automatically created by randomTrips.py)
if [ -f "$ROUTES_FILE" ]; then
    rm -f "$ROUTES_FILE"
    echo "✓ Trips generated successfully (routes.rou.xml cleaned up)"
else
    echo "✓ Trips generated successfully: $TRIPS_FILE"
fi
echo ""

# Step 3: Run the simulation
echo "[3/3] Starting SUMO simulation..."
echo "=========================================="
echo ""

cd "$PROJECT_DIR"
python simulation.py

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✓ Simulation completed successfully!"
    echo "=========================================="
    echo ""
    echo "Output files:"
    echo "  - Trip info: $MAP_DIR/tripinfos.xml"
    echo "  - Statistics: $MAP_DIR/stats.xml"
    echo ""
else
    echo ""
    echo "=========================================="
    echo "✗ Simulation failed!"
    echo "=========================================="
    exit 1
fi
