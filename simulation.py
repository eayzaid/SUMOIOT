import traci
import time
from driversManagement import *
from sensorsScripts.speedRadar import RadarManager

# 1. Initialize radar system
# Using 'full' scan - simple and reliable for IoT demo
radar_manager = RadarManager('radars_config.json', method='full')
radar_manager.load_radars()

# 2. Start the simulation with GUI
# "sumo-gui" opens the window. Change to "sumo" to run without window.
sumoCmd = ["sumo-gui", "-c", "./ENSAM_MAP/config.sumocfg", "--start"]
traci.start(sumoCmd)

# 3. Add radars to the map (visual representation)
print("Adding speed radars to map...")
radar_manager.add_radars_to_map(traci)
print("✓ Radars added to map\n")

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

# Print radar statistics
radar_manager.print_summary()