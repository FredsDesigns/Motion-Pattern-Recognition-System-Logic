-- Motion Recognition System - Complete Database Setup
-- This file contains all SQL queries needed to set up the motion recognition database

-- Create and select the database
CREATE DATABASE IF NOT EXISTS motion_data;
USE motion_data;

-- Create the main sensor data table for storing motion readings
CREATE TABLE IF NOT EXISTS sensor_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    motion_label VARCHAR(50),
    accel_x FLOAT,
    accel_y FLOAT,
    accel_z FLOAT,
    gyro_x FLOAT,
    gyro_y FLOAT,
    gyro_z FLOAT,
    sequence_id VARCHAR(50)
);

-- Create the motion patterns reference table
CREATE TABLE IF NOT EXISTS motion_patterns (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) UNIQUE,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Insert the motion patterns we're using
INSERT INTO motion_patterns (name, description) VALUES
    ('resting', 'No significant movement, completely stationary'),
    ('idle', 'Minor movements, but not directed activity'),
    ('walking', 'Walking pace movement'),
    ('running', 'Running or jogging movement'),
    ('moving', 'General movement not matching other patterns');

-- Create user for application access
CREATE USER IF NOT EXISTS 'motion_app'@'localhost' IDENTIFIED BY 'motion123';

-- Grant privileges to the application user
GRANT ALL PRIVILEGES ON motion_data.* TO 'motion_app'@'localhost';
FLUSH PRIVILEGES;

-- Verify the setup
SELECT 'Database setup complete' AS status;
SELECT USER(), CURRENT_USER() AS current_connection;
SHOW TABLES;
SELECT name, description FROM motion_patterns;

-- Sample queries for data analysis
-- Uncomment and use as needed:

-- 1. Count records by motion type
-- SELECT motion_label, COUNT(*) as count FROM sensor_data GROUP BY motion_label;

-- 2. Get most recent data
-- SELECT * FROM sensor_data ORDER BY timestamp DESC LIMIT 10;

-- 3. Get data from a specific time range
-- SELECT * FROM sensor_data 
-- WHERE timestamp BETWEEN '2025-03-31 00:00:00' AND '2025-04-01 23:59:59';

-- 4. Get sequences with significant running
-- SELECT sequence_id, COUNT(*) as count 
-- FROM sensor_data 
-- WHERE motion_label = 'running' 
-- GROUP BY sequence_id 
-- HAVING count > 10;