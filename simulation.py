import traci
import time
import uuid
import requests
from driversManagement import *
from sensorsScripts.speedRadar import RadarManager

# 1. Initialize radar system
# Generate unique simulation ID
simulation_id = str(uuid.uuid4())
print(f"Starting simulation with ID: {simulation_id}")

# Using 'full' scan - simple and reliable for IoT demo
radar_manager = RadarManager('radars_config.json', method='full', simulation_id=simulation_id)
radar_manager.load_radars()

# Notify backend of start
try:
    requests.post('http://localhost:5000/api/simulation/start', json={'simulation_id': simulation_id})
except:
    try:
        requests.post('http://backend:5000/api/simulation/start', json={'simulation_id': simulation_id})
    except:
        print("Warning: Could not notify backend of start")

import os

# 2. Start the simulation with GUI or Headless
# Check if running in Docker or explicitly requested headless
if os.environ.get('HEADLESS_MODE') == 'true':
    sumoBinary = "sumo"
else:
    sumoBinary = "sumo-gui"

sumoCmd = [sumoBinary, "-c", "./ENSAM_MAP/config.sumocfg", "--start"]
traci.start(sumoCmd)

# 3. Add radars to the map (visual representation)
print("Adding speed radars to map...")
radar_manager.add_radars_to_map(traci)
print("[INFO] Radars added to map\n")

step = 0
print("Starting simulation loop...\n")

while step < 3600:
    # Advance the simulation by one step
    traci.simulationStep()
    
    # Introduce realistic driver behaviors
    introduceNoiseToDrivers(traci)
    introduceRandomErrors(traci, error_probability=0.001)
    
    # Check all radars for speeding violations (every step for accuracy)
    radar_manager.check_all_vehicles(traci, step)
    
    # Introduce fatigue effects every 100 steps
    if step % 100 == 0:
        introduceFatigue(traci, step, fatigue_start_step=1800)
    
    step += 1
    # Add a tiny sleep so you can watch it happen in real-time (optional)
    time.sleep(0.01)

print("\nSimulation complete. Closing...")
traci.close()

# Notify backend of end
try:
    requests.post('http://localhost:5000/api/simulation/end', json={'simulation_id': simulation_id})
except:
    try:
        requests.post('http://backend:5000/api/simulation/end', json={'simulation_id': simulation_id})
    except:
        print("Warning: Could not notify backend of end")

# Print radar statistics
radar_manager.print_summary()