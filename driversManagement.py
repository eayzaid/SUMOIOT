import random

# Moroccan license plate generation
_used_plates = set()

def generate_moroccan_plate():
    """
    Generate a realistic Moroccan license plate.
    Format: NNNNN-L-NN (e.g., 12345-A-67, 98765-ب-12)
    Uses both Latin and Arabic letters for authenticity.
    """
    # Moroccan plates use Arabic letters: أ ب ج د ه و ز ح ط
    # Or Latin equivalents: A B C D E F G H I J K L M N O P Q R S T U V W X Y Z
    
    # Mix of Arabic and Latin letters (more realistic)
    arabic_letters = ['أ', 'ب', 'ج', 'د', 'ه', 'و', 'ز', 'ح']
    latin_letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'N', 'P', 'Q', 'R', 'S', 'T', 'V', 'W', 'X', 'Y', 'Z']
    
    # Generate unique plate
    attempts = 0
    while attempts < 100:
        # Choose between Arabic or Latin letter (70% Latin for better display compatibility)
        if random.random() < 0.7:
            letter = random.choice(latin_letters)
        else:
            letter = random.choice(arabic_letters)
        
        # Format: NNNNN-L-NN
        first_num = random.randint(10000, 99999)
        last_num = random.randint(10, 99)
        plate = f"{first_num}-{letter}-{last_num}"
        
        if plate not in _used_plates:
            _used_plates.add(plate)
            return plate
        
        attempts += 1
    
    # Fallback if somehow all plates are taken
    return f"{random.randint(10000, 99999)}-X-{random.randint(10, 99)}"


def get_vehicle_plate(traci, vehicle_id):
    """
    Get the Moroccan license plate for a vehicle.
    Returns the plate if set, otherwise returns vehicle_id.
    
    Args:
        traci: TraCI connection object
        vehicle_id: The SUMO vehicle ID
    
    Returns:
        str: License plate (e.g., "12345-A-67") or vehicle_id if not set
    """
    try:
        plate = traci.vehicle.getParameter(vehicle_id, "license_plate")
        return plate if plate else vehicle_id
    except:
        return vehicle_id


# This method introduces realistic noise to drivers with probabilistic behavior
def introduceNoiseToDrivers(traci):
    """
    Creates realistic driver diversity with multiple profiles and randomized parameters.
    Simulates real-world driver behavior spectrum from cautious to reckless.
    """
    new_cars = traci.simulation.getDepartedIDList()

    for car_id in new_cars:
        # Generate Moroccan license plate and rename vehicle
        moroccan_plate = generate_moroccan_plate()
        try:
            # Store original ID and rename to plate
            traci.vehicle.setParameter(car_id, "original_id", car_id)
            # Note: SUMO doesn't allow renaming vehicle IDs, but we can use the plate
            # in logging by storing it as a parameter
            traci.vehicle.setParameter(car_id, "license_plate", moroccan_plate)
        except:
            pass  # If renaming fails, continue with original ID
        
        # Roll dice to determine driver profile
        chance = random.random()  # 0.0 to 1.0
        
        if chance < 0.05:
            # === 5% RECKLESS (Very Dangerous) ===
            speed_factor = random.uniform(1.4, 1.7)       # 40-70% over limit
            imperfection = random.uniform(0.6, 1.0)       # Very erratic
            accel = random.uniform(5.5, 7.0)              # Aggressive acceleration
            decel = random.uniform(5.0, 6.5)              # Hard braking
            min_gap = random.uniform(0.5, 1.2)            # Dangerous following
            tau = random.uniform(0.3, 0.6)                # Quick reaction (risky)
            sigma = random.uniform(0.7, 1.0)              # High driver imperfection
            color = (255, 0, 0, 255)                      # RED
            profile = "RECKLESS"
            
        elif chance < 0.20:
            # === 15% AGGRESSIVE (Pushes limits) ===
            speed_factor = random.uniform(1.15, 1.35)     # 15-35% over limit
            imperfection = random.uniform(0.3, 0.5)       # Some weaving
            accel = random.uniform(3.5, 5.0)              # Quick acceleration
            decel = random.uniform(4.0, 5.5)              # Firm braking
            min_gap = random.uniform(1.5, 2.2)            # Follows close
            tau = random.uniform(0.6, 1.0)                # Fast reaction
            sigma = random.uniform(0.4, 0.6)              # Moderate imperfection
            color = (255, 100, 0, 255)                    # ORANGE-RED
            profile = "AGGRESSIVE"
            
        elif chance < 0.55:
            # === 35% NORMAL (Average driver) ===
            speed_factor = random.uniform(0.95, 1.15)     # -5% to +15% of limit
            imperfection = random.uniform(0.1, 0.3)       # Slight imperfection
            accel = random.uniform(2.5, 3.5)              # Normal acceleration
            decel = random.uniform(3.5, 5.0)              # Normal braking
            min_gap = random.uniform(2.0, 3.0)            # Safe following distance
            tau = random.uniform(1.0, 1.5)                # Standard reaction time
            sigma = random.uniform(0.3, 0.5)              # Normal driver error
            color = (0, 200, 255, 255)                    # CYAN (normal)
            profile = "NORMAL"
            
        elif chance < 0.80:
            # === 25% CAUTIOUS (Defensive driver) ===
            speed_factor = random.uniform(0.75, 0.95)     # 5-25% under limit
            imperfection = random.uniform(0.05, 0.15)     # Very smooth
            accel = random.uniform(1.8, 2.5)              # Gentle acceleration
            decel = random.uniform(3.0, 4.0)              # Gradual braking
            min_gap = random.uniform(3.0, 5.0)            # Large safety gap
            tau = random.uniform(1.5, 2.2)                # Slower, safer reaction
            sigma = random.uniform(0.1, 0.3)              # Low imperfection
            color = (0, 255, 0, 255)                      # GREEN
            profile = "CAUTIOUS"
            
        else:
            # === 20% ELDERLY/DISTRACTED (Very slow, erratic) ===
            speed_factor = random.uniform(0.60, 0.80)     # 20-40% under limit
            imperfection = random.uniform(0.4, 0.7)       # Erratic (distraction)
            accel = random.uniform(1.2, 2.0)              # Slow acceleration
            decel = random.uniform(2.5, 3.5)              # Gentle braking
            min_gap = random.uniform(4.0, 6.0)            # Extra safety distance
            tau = random.uniform(2.0, 3.0)                # Delayed reactions
            sigma = random.uniform(0.5, 0.8)              # High uncertainty
            color = (150, 150, 150, 255)                  # GRAY
            profile = "ELDERLY/DISTRACTED"
        
        # Apply all parameters to vehicle
        traci.vehicle.setSpeedFactor(car_id, speed_factor)
        traci.vehicle.setImperfection(car_id, imperfection)
        traci.vehicle.setAccel(car_id, accel)
        traci.vehicle.setDecel(car_id, decel)
        traci.vehicle.setMinGap(car_id, min_gap)
        traci.vehicle.setTau(car_id, tau)
        traci.vehicle.setMaxSpeed(car_id, 50.0)  # Max speed cap (m/s ~180 km/h)
        
        # Note: sigma is part of the car-following model, set during init if needed
        # traci.vehicle.setParameter(car_id, "sigma", str(sigma))
        
        traci.vehicle.setColor(car_id, color)
        
        # Log only interesting cases (not normal drivers to reduce spam)
        if profile != "NORMAL":
            print(f"[{profile}] {car_id} | Speed: {speed_factor:.2f}x | Gap: {min_gap:.1f}m | Tau: {tau:.2f}s")


def introduceRandomErrors(traci, error_probability=0.001):
    """
    Introduces random errors during simulation (sudden braking, lane errors, etc.)
    Call this each simulation step to simulate unexpected driver mistakes.
    
    Args:
        traci: TraCI connection object
        error_probability: Chance per vehicle per step (default 0.1% = 1 in 1000)
    """
    vehicle_ids = traci.vehicle.getIDList()
    
    for car_id in vehicle_ids:
        if random.random() < error_probability:
            error_type = random.choice(['sudden_brake', 'speed_change', 'distraction'])
            
            if error_type == 'sudden_brake':
                # Simulate panic braking (emergency stop)
                current_speed = traci.vehicle.getSpeed(car_id)
                traci.vehicle.slowDown(car_id, current_speed * 0.3, 1000)  # Reduce to 30% in 1 sec
                print(f"[WARN] {car_id}: SUDDEN BRAKE!")
                
            elif error_type == 'speed_change':
                # Sudden acceleration or deceleration (driver error/distraction)
                new_speed_factor = random.uniform(0.7, 1.4)
                traci.vehicle.setSpeedFactor(car_id, new_speed_factor)
                print(f"[WARN] {car_id}: Speed fluctuation ({new_speed_factor:.2f}x)")
                
            elif error_type == 'distraction':
                # Temporarily increase imperfection (weaving, delayed reaction)
                traci.vehicle.setImperfection(car_id, random.uniform(0.6, 0.9))
                print(f"[WARN] {car_id}: Distracted!")


def introduceFatigue(traci, simulation_step, fatigue_start_step=5000):
    """
    Simulates driver fatigue over time - drivers get slower and more erratic.
    Call this periodically (e.g., every 100 steps) for long simulations.
    
    Args:
        traci: TraCI connection object
        simulation_step: Current simulation step
        fatigue_start_step: When fatigue effects begin
    """
    if simulation_step < fatigue_start_step:
        return
    
    vehicle_ids = traci.vehicle.getIDList()
    fatigue_factor = min((simulation_step - fatigue_start_step) / 10000.0, 0.3)  # Max 30% effect
    
    for car_id in vehicle_ids:
        if random.random() < 0.05:  # 5% of drivers per check affected
            current_speed_factor = traci.vehicle.getSpeedFactor(car_id)
            new_speed_factor = max(0.5, current_speed_factor - fatigue_factor * random.uniform(0.1, 0.3))
            traci.vehicle.setSpeedFactor(car_id, new_speed_factor)
            
            # Increase imperfection (tired = less focused)
            current_imperfection = traci.vehicle.getImperfection(car_id)
            new_imperfection = min(1.0, current_imperfection + fatigue_factor * random.uniform(0.1, 0.2))
            traci.vehicle.setImperfection(car_id, new_imperfection)
