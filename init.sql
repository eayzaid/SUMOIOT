CREATE TABLE IF NOT EXISTS violations (
    id SERIAL PRIMARY KEY,
    simulation_id VARCHAR(50),
    radar_id VARCHAR(50) NOT NULL,
    vehicle_id VARCHAR(50) NOT NULL,
    license_plate VARCHAR(50),
    timestamp INTEGER NOT NULL,
    location_x FLOAT,
    location_y FLOAT,
    speed_limit_kmh FLOAT,
    actual_speed_kmh FLOAT,
    overspeed_kmh FLOAT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS simulations (
    simulation_id VARCHAR(50) PRIMARY KEY,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    status VARCHAR(20) DEFAULT 'RUNNING'
);
