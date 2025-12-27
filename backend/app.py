from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import os
import time
import docker

app = Flask(__name__)
CORS(app)

def get_db_connection():
    retries = 5
    while retries > 0:
        try:
            conn = psycopg2.connect(
                host=os.environ.get('DB_HOST', 'db'),
                database=os.environ.get('DB_NAME', 'sumo_db'),
                user=os.environ.get('DB_USER', 'postgres'),
                password=os.environ.get('DB_PASSWORD', 'postgres')
            )
            return conn
        except psycopg2.OperationalError:
            retries -= 1
            print(f"DB connection failed, retrying... ({retries} left)")
            time.sleep(2)
    return None

@app.route('/api/violations', methods=['GET'])
def get_violations():
    simulation_id = request.args.get('simulation_id')
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    
    cur = conn.cursor()
    
    if simulation_id:
        cur.execute('SELECT * FROM violations WHERE simulation_id = %s ORDER BY created_at DESC LIMIT 1000;', (simulation_id,))
    else:
        cur.execute('SELECT * FROM violations ORDER BY created_at DESC LIMIT 1000;')
        
    rows = cur.fetchall()
    
    violations = []
    for row in rows:
        violations.append({
            "id": row[0],
            "simulation_id": row[1],
            "radar_id": row[2],
            "vehicle_id": row[3],
            "license_plate": row[4],
            "timestamp": row[5],
            "location_x": row[6],
            "location_y": row[7],
            "speed_limit_kmh": row[8],
            "actual_speed_kmh": row[9],
            "overspeed_kmh": row[10],
            "description": row[11],
            "created_at": row[12]
        })
    
    cur.close()
    conn.close()
    return jsonify(violations)

@app.route('/api/violations', methods=['POST'])
def add_violation():
    data = request.json
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    
    cur = conn.cursor()
    try:
        cur.execute(
            """INSERT INTO violations (simulation_id, radar_id, vehicle_id, license_plate, timestamp, 
               location_x, location_y, speed_limit_kmh, actual_speed_kmh, overspeed_kmh, description)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (data.get('simulation_id'), data['radar_id'], data['vehicle_id'], data['license_plate'], data['timestamp'],
             data['location'][0], data['location'][1], data['speed_limit_kmh'], 
             data['actual_speed_kmh'], data['overspeed_kmh'], data['description'])
        )
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"status": "success"}), 201
    except Exception as e:
        print(f"Error inserting violation: {e}")
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({"error": str(e)}), 400

@app.route('/api/simulation/start', methods=['POST'])
def start_simulation():
    data = request.json
    simulation_id = data.get('simulation_id')
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO simulations (simulation_id, status) VALUES (%s, 'RUNNING')",
            (simulation_id,)
        )
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"status": "success"}), 201
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({"error": str(e)}), 400

@app.route('/api/simulation/end', methods=['POST'])
def end_simulation():
    data = request.json
    simulation_id = data.get('simulation_id')
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE simulations SET end_time = CURRENT_TIMESTAMP, status = 'COMPLETED' WHERE simulation_id = %s",
            (simulation_id,)
        )
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
    cur.close()
    conn.close()
    return jsonify({"status": "success"}), 200

@app.route('/api/control/spawn-simulation', methods=['POST'])
def spawn_simulation():
    try:
        client = docker.from_env()
        
        # Spawn a new container
        container = client.containers.run(
            image="sumoiot-simulation:latest",
            detach=True,
            auto_remove=True,
            network="sumoiot_default",
            environment={
                "SUMO_HOME": "/usr/share/sumo",
                "HEADLESS_MODE": "true"
            },
            labels={"com.sumoiot.role": "simulation"}
        )
        
        return jsonify({"status": "success", "message": f"New simulation spawned: {container.short_id}"}), 200
    except Exception as e:
        print(f"Error spawning simulation: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/simulations', methods=['GET'])
def get_simulations():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    
    cur = conn.cursor()
    # Get simulations from the dedicated table
    cur.execute('''
        SELECT s.simulation_id, s.start_time, s.end_time, s.status, COUNT(v.id) as violation_count 
        FROM simulations s
        LEFT JOIN violations v ON s.simulation_id = v.simulation_id
        GROUP BY s.simulation_id, s.start_time, s.end_time, s.status
        ORDER BY s.start_time DESC
    ''')
    rows = cur.fetchall()
    
    simulations = []
    for row in rows:
        simulations.append({
            "simulation_id": row[0],
            "start_time": row[1],
            "end_time": row[2],
            "status": row[3],
            "violation_count": row[4]
        })
    
    cur.close()
    conn.close()
    return jsonify(simulations)

@app.route('/api/driver/<plate>', methods=['GET'])
def get_driver_history(plate):
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    
    cur = conn.cursor()
    cur.execute('SELECT * FROM violations WHERE license_plate = %s ORDER BY created_at DESC;', (plate,))
    rows = cur.fetchall()
    
    violations = []
    for row in rows:
        violations.append({
            "id": row[0],
            "simulation_id": row[1],
            "radar_id": row[2],
            "vehicle_id": row[3],
            "license_plate": row[4],
            "timestamp": row[5],
            "location_x": row[6],
            "location_y": row[7],
            "speed_limit_kmh": row[8],
            "actual_speed_kmh": row[9],
            "overspeed_kmh": row[10],
            "description": row[11],
            "created_at": row[12]
        })
    
    cur.close()
    conn.close()
    return jsonify(violations)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
