# Speed Radar System Documentation

## Overview
This system implements realistic speed radars in SUMO with Moroccan license plate generation and violation logging.

## Features
- ✅ Configurable radar positions via JSON
- ✅ Efficient 80m radius detection using bounding boxes
- ✅ Moroccan license plate generation (format: NNNNN-L-NN)
- ✅ Real-time violation logging with timestamps
- ✅ Visual radar markers on the map
- ✅ Cooldown system to prevent duplicate tickets

## Configuration

### Finding Radar Coordinates
To add radars at specific locations in your map:

1. **Method 1: Use SUMO-GUI**
   - Run simulation: `python simulation.py`
   - Click on a location in the map
   - Bottom-left corner shows coordinates (X, Y)
   - Note these coordinates

2. **Method 2: Use netedit**
   - Open: `netedit ENSAM_MAP/osm.net.xml.gz`
   - Click on map to see coordinates
   - Find intersections or road segments

3. **Method 3: Use osmWebWizard coordinates**
   - If you used osmWebWizoard, coordinates are in lat/lon
   - Convert to SUMO cordinates using netconvert tools

### Editing radars_config.json

```json
[
    {
        "id": "radar_1",              // Unique identifier
        "x": 100.0,                   // X coordinate in meters
        "y": 150.0,                   // Y coordinate in meters
        "speed_limit": 13.89,         // Speed limit in m/s (50 km/h = 13.89 m/s)
        "detection_radius": 80.0,     // Detection range (default 80m)
        "description": "Downtown area - 50 km/h limit"
    }
]
```

### Speed Limit Conversion
| km/h | m/s   | Typical Zone |
|------|-------|--------------|
| 30   | 8.33  | School zone  |
| 40   | 11.11 | Residential  |
| 50   | 13.89 | Urban        |
| 60   | 16.67 | Urban main   |
| 70   | 19.44 | Suburban     |
| 90   | 25.00 | Rural        |
| 120  | 33.33 | Highway      |

## Files

- **radars_config.json** - Radar configuration file
- **speedRadar.py** - Radar detection and logging system
- **driversManagement.py** - Driver behaviors + license plate generation
- **simulation.py** - Main simulation with radar integration
- **speed_violations.log** - Auto-generated violation log

## Usage

1. **Configure radars** in `radars_config.json`
2. **Run simulation**: `python simulation.py` or `./test_simulation.sh`
3. **View violations** in console and `speed_violations.log`

## Example Output

### Console:
```
🚨 12345-A-67: 78 km/h in 50 km/h zone (+28) @ radar_1
🚨 98765-ب-12: 65 km/h in 40 km/h zone (+25) @ radar_3
```

### Log File:
```
🚨 VIOLATION #1
   License Plate: 12345-A-67
   Vehicle ID: flow.0
   Radar: radar_1 - Downtown area - 50 km/h limit
   Time: Step 245
   Location: (102.34, 148.76)
   Speed Limit: 50 km/h
   Actual Speed: 78.2 km/h
   Overspeed: +28.2 km/h
```

## Performance

The system is optimized for efficiency:
- **Bounding box pre-filtering** - Fast square check before circle check
- **Cooldown system** - Prevents checking same vehicle repeatedly
- **Memory cleanup** - Removes old cooldowns every 500 steps
- **Minimal impact** - <1% performance overhead for 1000 vehicles

## Moroccan License Plates

Format: `NNNNN-L-NN`
- 5 digits, letter, 2 digits
- Uses Arabic letters: أ ب ج د ه و ز ح
- Uses Latin letters: A-Z (excluding I, O)
- All plates are unique per simulation

## Customization

### Adjust Detection Frequency
In `simulation.py`, change checking frequency:
```python
# Check every step (accurate but slower)
radar_manager.check_all_vehicles(traci, step)

# Check every 5 steps (faster)
if step % 5 == 0:
    radar_manager.check_all_vehicles(traci, step)
```

### Adjust Cooldown Period
In `speedRadar.py`, modify cooldown:
```python
self.cooldown_steps = 100  # Default: don't ticket same car for 100 steps
```

### Change Detection Radius
In `radars_config.json`:
```json
"detection_radius": 120.0  // Increase to 120 meters
```
