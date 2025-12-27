import json
import requests
import math
from datetime import datetime
from driversManagement import get_vehicle_plate


class SpeedRadar:
    """
    Represents a speed radar sensor at a fixed location.
    Efficiently detects speeding vehicles within detection radius.
    """
    
    def __init__(self, radar_id, x, y, speed_limit, detection_radius=80.0, description="", simulation_id=None):
        self.id = radar_id
        self.simulation_id = simulation_id
        self.x = x
        self.y = y
        self.speed_limit = speed_limit  # in m/s
        self.detection_radius = detection_radius
        self.description = description
        
        # For efficiency: bounding box (square) is faster than circle check
        self.bbox_min_x = x - detection_radius
        self.bbox_max_x = x + detection_radius
        self.bbox_min_y = y - detection_radius
        self.bbox_max_y = y + detection_radius
        
        # Track violations to avoid duplicate tickets for same vehicle
        self.cooldown_steps = 100  # Don't ticket same vehicle for 100 steps
        self.violation_cooldowns = {}  # {vehicle_id: step_when_caught}
        
        # Edge-based optimization: cache nearby edges (populated at runtime)
        self.nearby_edges = []  # List of edge IDs near this radar
        self.edges_initialized = False
        
        # Statistics
        self.total_violations = 0
        self.total_checks = 0
    
    def find_nearby_edges(self, traci):
        """
        Find all edges within detection radius of this radar.
        Called once at startup - O(edges) but only runs once.
        """
        if self.edges_initialized:
            return
        
        all_edges = traci.edge.getIDList()
        
        for edge_id in all_edges:
            # Skip internal edges (junctions)
            if edge_id.startswith(':'):
                continue
            
            try:
                # Get all lanes of this edge and check their shapes
                lane_count = traci.edge.getLaneNumber(edge_id)
                
                for lane_idx in range(lane_count):
                    lane_id = f"{edge_id}_{lane_idx}"
                    try:
                        # Lane shape is more accurate than edge shape
                        shape = traci.lane.getShape(lane_id)
                        
                        # Check if any point of lane is within detection radius
                        for point in shape:
                            if self.is_in_detection_zone(point[0], point[1]):
                                self.nearby_edges.append(edge_id)
                                break  # Edge is nearby
                        
                        if edge_id in self.nearby_edges:
                            break  # Already found, check next edge
                    except:
                        pass
            except:
                pass
        
        self.edges_initialized = True
        if len(self.nearby_edges) > 0:
            print(f"  * {self.id}: Found {len(self.nearby_edges)} nearby edges")
        else:
            print(f"  [WARN] {self.id}: NO nearby edges found! Check radar coordinates (x={self.x}, y={self.y})")
    
    def get_nearby_vehicles(self, traci):
        """
        Get vehicles only on nearby edges - MUCH faster than full scan!
        Returns set of vehicle IDs.
        """
        nearby_vehicles = set()
        
        for edge_id in self.nearby_edges:
            try:
                vehicles_on_edge = traci.edge.getLastStepVehicleIDs(edge_id)
                nearby_vehicles.update(vehicles_on_edge)
            except:
                pass
        
        return nearby_vehicles
    
    def is_in_detection_zone(self, vehicle_x, vehicle_y):
        """
        Efficiently check if vehicle is within detection radius.
        First checks bounding box (fast), then exact distance (slower).
        """
        # Fast bounding box check first
        if not (self.bbox_min_x <= vehicle_x <= self.bbox_max_x and
                self.bbox_min_y <= vehicle_y <= self.bbox_max_y):
            return False
        
        # Exact circle check only if inside bounding box
        distance = math.sqrt((vehicle_x - self.x)**2 + (vehicle_y - self.y)**2)
        return distance <= self.detection_radius
    
    def check_vehicle(self, traci, vehicle_id, current_step):
        """
        Check if a vehicle is speeding within detection zone.
        Returns violation info dict if violation detected, None otherwise.
        """
        self.total_checks += 1
        
        # Check cooldown - don't ticket same vehicle repeatedly
        if vehicle_id in self.violation_cooldowns:
            if current_step - self.violation_cooldowns[vehicle_id] < self.cooldown_steps:
                return None
        
        try:
            # Get vehicle position
            vehicle_x, vehicle_y = traci.vehicle.getPosition(vehicle_id)
            
            # Quick spatial check
            if not self.is_in_detection_zone(vehicle_x, vehicle_y):
                return None
            
            # Vehicle is in range - check speed
            current_speed = traci.vehicle.getSpeed(vehicle_id)
            
            if current_speed > self.speed_limit:
                # VIOLATION DETECTED!
                overspeed = current_speed - self.speed_limit
                overspeed_kmh = overspeed * 3.6
                
                # Record violation
                self.violation_cooldowns[vehicle_id] = current_step
                self.total_violations += 1
                
                # Get license plate for logging
                license_plate = get_vehicle_plate(traci, vehicle_id)
                
                violation = {
                    'simulation_id': self.simulation_id,
                    'radar_id': self.id,
                    'vehicle_id': vehicle_id,
                    'license_plate': license_plate,
                    'timestamp': current_step,
                    'location': (vehicle_x, vehicle_y),
                    'speed_limit_ms': self.speed_limit,
                    'speed_limit_kmh': self.speed_limit * 3.6,
                    'actual_speed_ms': current_speed,
                    'actual_speed_kmh': current_speed * 3.6,
                    'overspeed_kmh': overspeed_kmh,
                    'description': self.description
                }
                
                return violation
        except:
            # Vehicle might have left simulation
            pass
        
        return None
    
    def cleanup_old_cooldowns(self, current_step):
        """Remove expired cooldowns to free memory"""
        expired = [vid for vid, step in self.violation_cooldowns.items() 
                   if current_step - step >= self.cooldown_steps]
        for vid in expired:
            del self.violation_cooldowns[vid]


class RadarManager:
    """
    Manages all speed radars in the simulation.
    Handles loading, checking, and logging violations.
    
    Detection methods (in order of preference):
    1. Edge-based: Query only vehicles on nearby edges (fastest, simplest)
    2. Context subscriptions: TraCI auto-filters nearby vehicles
    3. Full scan: Check all vehicles (slowest, fallback)
    """
    
    # Detection method options
    METHOD_EDGE_BASED = 'edge'           # Fastest: query vehicles by edge
    METHOD_CONTEXT_SUB = 'subscription'  # Fast: TraCI context subscriptions
    METHOD_FULL_SCAN = 'full'            # Slow: check all vehicles
    
    def __init__(self, config_file='radars_config.json', method='edge', simulation_id=None):
        self.radars = []
        self.config_file = config_file
        self.simulation_id = simulation_id
        self.violations_log = []
        self.log_file = 'speed_violations.log'
        self.detection_method = method
        self.initialized = False
        
        # Initialize log file
        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write("=" * 100 + "\n")
            f.write(f"SPEED RADAR VIOLATIONS LOG - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 100 + "\n\n")
    
    def load_radars(self):
        """Load radar configurations from JSON file"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                radars_data = json.load(f)
            
            for radar_data in radars_data:
                radar = SpeedRadar(
                    radar_id=radar_data['id'],
                    x=radar_data['x'],
                    y=radar_data['y'],
                    speed_limit=radar_data['speed_limit'],
                    detection_radius=radar_data.get('detection_radius', 80.0),
                    description=radar_data.get('description', ''),
                    simulation_id=self.simulation_id
                )
                self.radars.append(radar)
            
            print(f"[INFO] Loaded {len(self.radars)} speed radars from {self.config_file}")
            for radar in self.radars:
                speed_kmh = radar.speed_limit * 3.6
                print(f"  * {radar.id} at ({radar.x:.1f}, {radar.y:.1f}) - "
                      f"Limit: {speed_kmh:.0f} km/h - {radar.description}")
            return True
        
        except FileNotFoundError:
            print(f"[WARN] Warning: {self.config_file} not found. No radars loaded.")
            return False
        except json.JSONDecodeError as e:
            print(f"[ERROR] Error parsing {self.config_file}: {e}")
            return False
    
    def add_radars_to_map(self, traci):
        """
        Visually add radar POIs to SUMO map and initialize detection method.
        Creates polygons to show radar locations.
        """
        print(f"Initializing radars (method: {self.detection_method})...")
        
        for radar in self.radars:
            try:
                # Create circular polygon around radar position
                num_points = 12
                radius = 10  # Visual radius (not detection radius)
                points = []
                
                for i in range(num_points):
                    angle = 2 * math.pi * i / num_points
                    px = radar.x + radius * math.cos(angle)
                    py = radar.y + radius * math.sin(angle)
                    points.append((px, py))
                
                # Add radar as polygon (red circle)
                traci.polygon.add(
                    polygonID=f"radar_{radar.id}",
                    shape=points,
                    color=(255, 0, 0, 180),  # Red with transparency
                    layer=100,
                    polygonType="radar"
                )
                
            except Exception as e:
                print(f"[WARN] Could not add visual for {radar.id}: {e}")
        
        # Initialize detection method
        if self.detection_method == self.METHOD_EDGE_BASED:
            # Find nearby edges for each radar (one-time operation)
            print("Finding nearby edges for each radar...")
            for radar in self.radars:
                radar.find_nearby_edges(traci)
            print(f"[INFO] Edge-based detection active (fastest)")
            
        elif self.detection_method == self.METHOD_CONTEXT_SUB:
            # Setup context subscriptions
            for radar in self.radars:
                try:
                    traci.poi.add(
                        poiID=f"poi_{radar.id}",
                        x=radar.x,
                        y=radar.y,
                        color=(255, 0, 0, 255),
                        layer=101,
                        poiType="radar_sensor"
                    )
                    traci.poi.subscribeContext(
                        f"poi_{radar.id}",
                        traci.constants.CMD_GET_VEHICLE_VARIABLE,
                        radar.detection_radius,
                        [traci.constants.VAR_SPEED, traci.constants.VAR_POSITION]
                    )
                except Exception as e:
                    print(f"[WARN] Context subscription failed for {radar.id}: {e}")
            print(f"[INFO] Context subscriptions active (fast)")
        else:
            print(f"[INFO] Full scan mode (slower but compatible)")
        
        self.initialized = True
    
    def check_all_vehicles(self, traci, current_step):
        """
        Efficiently check vehicles against radars using the selected method.
        
        Methods by speed:
        1. Edge-based: ~10-50x faster than full scan
        2. Context subscriptions: ~10-100x faster than full scan
        3. Full scan: O(vehicles * radars) - slowest
        """
        if self.detection_method == self.METHOD_EDGE_BASED:
            self._check_with_edge_based(traci, current_step)
        elif self.detection_method == self.METHOD_CONTEXT_SUB:
            self._check_with_subscriptions(traci, current_step)
        else:
            self._check_with_full_scan(traci, current_step)
        
        # Periodic cleanup of old cooldowns
        if current_step % 500 == 0:
            for radar in self.radars:
                radar.cleanup_old_cooldowns(current_step)
    
    def _check_with_edge_based(self, traci, current_step):
        """
        Check vehicles using edge-based spatial indexing.
        Only queries vehicles on edges near each radar.
        FASTEST method - simple and efficient!
        """
        for radar in self.radars:
            # Get vehicles only on nearby edges
            nearby_vehicles = radar.get_nearby_vehicles(traci)
            
            for vehicle_id in nearby_vehicles:
                violation = radar.check_vehicle(traci, vehicle_id, current_step)
                if violation:
                    self._log_violation(violation)
        
        # Periodic cleanup of old cooldowns
        if current_step % 500 == 0:
            for radar in self.radars:
                radar.cleanup_old_cooldowns(current_step)
    
    def _check_with_subscriptions(self, traci, current_step):
        """
        Check vehicles using efficient context subscriptions.
        10-100x faster than full scan for large simulations!
        """
        for radar in self.radars:
            try:
                # Get context subscription results - only vehicles near this radar
                nearby_vehicles = traci.poi.getContextSubscriptionResults(f"poi_{radar.id}")
                
                if nearby_vehicles:
                    for vehicle_id, vehicle_data in nearby_vehicles.items():
                        # Check cooldown first
                        if vehicle_id in radar.violation_cooldowns:
                            if current_step - radar.violation_cooldowns[vehicle_id] < radar.cooldown_steps:
                                continue
                        
                        # Get speed and position from subscription data
                        speed = vehicle_data.get(traci.constants.VAR_SPEED, 0)
                        position = vehicle_data.get(traci.constants.VAR_POSITION, (0, 0))
                        
                        # Check if actually in detection zone (subscription gives approximate radius)
                        if not radar.is_in_detection_zone(position[0], position[1]):
                            continue
                        
                        # Check for speeding
                        if speed > radar.speed_limit:
                            overspeed_kmh = (speed - radar.speed_limit) * 3.6
                            radar.violation_cooldowns[vehicle_id] = current_step
                            radar.total_violations += 1
                            
                            license_plate = get_vehicle_plate(traci, vehicle_id)
                            
                            violation = {
                                'simulation_id': radar.simulation_id,
                                'radar_id': radar.id,
                                'vehicle_id': vehicle_id,
                                'license_plate': license_plate,
                                'timestamp': current_step,
                                'location': position,
                                'speed_limit_ms': radar.speed_limit,
                                'speed_limit_kmh': radar.speed_limit * 3.6,
                                'actual_speed_ms': speed,
                                'actual_speed_kmh': speed * 3.6,
                                'overspeed_kmh': overspeed_kmh,
                                'description': radar.description
                            }
                            
                            self._log_violation(violation)
            except Exception as e:
                # If subscription fails, fall back to full scan for this radar
                print(f"[WARN] Subscription failed for {radar.id}, using fallback: {e}")
                self._check_radar_full_scan(traci, radar, current_step)
    
    def _check_with_full_scan(self, traci, current_step):
        """
        Check all vehicles against all radars.
        Simple and reliable method for demos.
        """
        vehicle_ids = traci.vehicle.getIDList()
        
        if not vehicle_ids:
            return
        
        for vehicle_id in vehicle_ids:
            for radar in self.radars:
                violation = radar.check_vehicle(traci, vehicle_id, current_step)
                if violation:
                    self._log_violation(violation)
    
    def _check_radar_full_scan(self, traci, radar, current_step):
        """Check a single radar using full scan (used as fallback)"""
        vehicle_ids = traci.vehicle.getIDList()
        for vehicle_id in vehicle_ids:
            violation = radar.check_vehicle(traci, vehicle_id, current_step)
            if violation:
                self._log_violation(violation)
    
    def _log_violation(self, violation):
        """Log a speed violation to file, console, and backend API"""
        self.violations_log.append(violation)
        
        # Format log message
        log_msg = (
            f"[VIOLATION] #{len(self.violations_log)}\n"
            f"   License Plate: {violation['license_plate']}\n"
            f"   Vehicle ID: {violation['vehicle_id']}\n"
            f"   Radar: {violation['radar_id']} - {violation['description']}\n"
            f"   Time: Step {violation['timestamp']}\n"
            f"   Location: ({violation['location'][0]:.2f}, {violation['location'][1]:.2f})\n"
            f"   Speed Limit: {violation['speed_limit_kmh']:.0f} km/h\n"
            f"   Actual Speed: {violation['actual_speed_kmh']:.1f} km/h\n"
            f"   Overspeed: +{violation['overspeed_kmh']:.1f} km/h\n"
            f"{'-' * 80}\n"
        )
        
        # Write to file
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_msg)
        
        # Print to console (shorter version)
        print(f"[VIOLATION] {violation['license_plate']}: {violation['actual_speed_kmh']:.0f} km/h "
              f"in {violation['speed_limit_kmh']:.0f} km/h zone (+{violation['overspeed_kmh']:.0f}) "
              f"@ {violation['radar_id']}")

        # Send to backend
        try:
            # Try localhost first (local run), then 'backend' (docker run)
            # In a real scenario, this should be configurable via env var
            api_url = "http://localhost:5000/api/violations"
            try:
                requests.post(api_url, json=violation, timeout=1)
            except requests.exceptions.ConnectionError:
                # If localhost fails, try docker service name
                api_url = "http://backend:5000/api/violations"
                requests.post(api_url, json=violation, timeout=1)
        except Exception as e:
            print(f"[WARN] Failed to send violation to backend: {e}")
    
    def get_statistics(self):
        """Get overall statistics for all radars"""
        total_violations = sum(r.total_violations for r in self.radars)
        total_checks = sum(r.total_checks for r in self.radars)
        
        stats = {
            'total_radars': len(self.radars),
            'total_violations': total_violations,
            'total_checks': total_checks,
            'violations_by_radar': {r.id: r.total_violations for r in self.radars}
        }
        
        return stats
    
    def print_summary(self):
        """Print summary statistics at end of simulation"""
        stats = self.get_statistics()
        
        print("\n" + "=" * 80)
        print("SPEED RADAR SUMMARY")
        print("=" * 80)
        print(f"Total Radars: {stats['total_radars']}")
        print(f"Total Violations: {stats['total_violations']}")
        print(f"Total Vehicle Checks: {stats['total_checks']}")
        print("\nViolations by Radar:")
        for radar_id, count in stats['violations_by_radar'].items():
            print(f"  * {radar_id}: {count} violations")
        print("=" * 80)
        print(f"Full log saved to: {self.log_file}")
