import serial
import time
import mysql.connector
import numpy as np
from datetime import datetime
from collections import deque

# MySQL Database Configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'motion_app',
    'password': 'motion123',
    'database': 'motion_data'
}

# Serial port configuration
SERIAL_PORT = 'COM4'  # Update this to match your Arduino port
BAUD_RATE = 115200

# Motion recognition parameters
WINDOW_SIZE = 20  # Number of samples to consider for pattern recognition
SAMPLING_RATE = 10  # Hz (matches Arduino's 100ms interval)

class SimpleMotionRecognizer:
    """Simplified motion recognizer focusing on idle, walking, and running."""
    
    def __init__(self):
        """Initialize with calibrated thresholds for the reliable motion types."""
        # Baseline values for your specific sensor
        self.baseline_accel = 9.82  # Your sensor's gravity baseline
        
        # Idle thresholds - keeping these exact since they work perfectly
        self.idle_accel_range = 0.05  # Maximum deviation from baseline to be considered idle
        self.idle_std_max = 0.03     # Maximum standard deviation for idle
        self.idle_gyro_max = 0.05    # Maximum gyro reading for idle
        
        # Movement thresholds - these work well according to feedback
        self.walk_threshold_min = 10.3  # Minimum for walking
        self.walk_threshold_max = 14.0  # Maximum for walking
        self.run_threshold = 14.0       # Above this is running
        
        # Buffer for recent samples
        self.buffer = deque(maxlen=WINDOW_SIZE)
        
        # Debug mode
        self.debug = True
        
        # Output throttling
        self.output_counter = 0
        self.output_frequency = 5  # Only print every X readings
    
    def add_sample(self, accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z):
        """Add a new motion sample to the buffer."""
        self.buffer.append({
            'accel_x': accel_x,
            'accel_y': accel_y,
            'accel_z': accel_z,
            'gyro_x': gyro_x,
            'gyro_y': gyro_y,
            'gyro_z': gyro_z
        })
    
    def recognize_pattern(self):
        """Analyze buffer and determine the motion state."""
        self.output_counter += 1
        print_output = (self.output_counter % self.output_frequency == 0)
        
        if len(self.buffer) < WINDOW_SIZE // 2:
            return "collecting_data"  # Not enough data yet
            
        # Extract features from buffer
        accel_magnitudes = []
        gyro_magnitudes = []
        
        for sample in self.buffer:
            # Calculate acceleration and gyroscope magnitudes
            accel_mag = np.sqrt(sample['accel_x']**2 + sample['accel_y']**2 + sample['accel_z']**2)
            gyro_mag = np.sqrt(sample['gyro_x']**2 + sample['gyro_y']**2 + sample['gyro_z']**2)
            
            accel_magnitudes.append(accel_mag)
            gyro_magnitudes.append(gyro_mag)
            
        # Statistical features
        accel_mean = np.mean(accel_magnitudes)
        accel_std = np.std(accel_magnitudes)
        accel_max = np.max(accel_magnitudes)
        
        gyro_mean = np.mean(gyro_magnitudes)
        
        # Calculate acceleration change over time (first derivative)
        accel_changes = [abs(accel_magnitudes[i] - accel_magnitudes[i-1]) 
                         for i in range(1, len(accel_magnitudes))]
        mean_accel_change = np.mean(accel_changes) if accel_changes else 0
        
        # Debug print features if enabled (throttled)
        if self.debug and print_output:
            print(f"\nFEATURES: accel_mean={accel_mean:.2f}, accel_std={accel_std:.2f}, " +
                  f"accel_max={accel_max:.2f}, gyro_mean={gyro_mean:.2f}, change={mean_accel_change:.2f}")
        
        # ----- MOTION DETECTION LOGIC -----
        
        # FIRST CHECK: Is it idle? (very specific criteria that worked well)
        if (abs(accel_mean - self.baseline_accel) < self.idle_accel_range and
            accel_std < self.idle_std_max and
            gyro_mean < self.idle_gyro_max):
            return "resting"
        
        # Detect running (high consistent acceleration)
        if accel_mean > self.run_threshold:
            return "running"
            
        # Detect walking (moderate consistent acceleration)
        if self.walk_threshold_min < accel_mean < self.walk_threshold_max:
            return "walking"
            
        # Any other motion that's not idle, walking, or running is "moving"
        return "idle"

def read_and_recognize():
    """Read sensor data and perform motion recognition."""
    try:
        # Connect to database
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Open serial connection
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"Connected to {SERIAL_PORT} at {BAUD_RATE} baud")
        
        # Generate a sequence ID based on timestamp
        sequence_id = datetime.now().strftime("%Y%m%d%H%M%S")
        print(f"Starting motion recognition session: {sequence_id}")
        
        # Initialize motion recognizer
        recognizer = SimpleMotionRecognizer()
        
        # Wait for serial connection to stabilize
        time.sleep(2)
        
        # Add minimal debouncing for stability
        current_motion = "idle"
        motion_count = 0
        
        # Print setup instructions
        print("\n*** SIMPLIFIED MOTION RECOGNITION SYSTEM ***")
        print("MOTION TYPES:")
        print("- IDLE: No significant movement")
        print("- WALKING: Walking pace movement")
        print("- RUNNING: Running or jogging movement")
        print("- MOVING: Other unclassified movements")
        print("\nPress Ctrl+C to stop\n")
        
        try:
            last_display_time = time.time()
            display_interval = 0.5  # seconds
            
            while True:
                if ser.in_waiting > 0:
                    # Read line from serial port
                    line = ser.readline().decode('utf-8').strip()
                    
                    try:
                        # Parse CSV formatted data
                        parts = line.split(',')
                        if len(parts) == 8:  # Ensure we have all expected values
                            arduino_timestamp = int(parts[0])
                            accel_x = float(parts[1])
                            accel_y = float(parts[2])
                            accel_z = float(parts[3])
                            gyro_x = float(parts[4])
                            gyro_y = float(parts[5])
                            gyro_z = float(parts[6])
                            temperature = float(parts[7])
                            
                            # Add sample to motion recognizer
                            recognizer.add_sample(accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z)
                            
                            # Perform motion recognition
                            detected_motion = recognizer.recognize_pattern()
                            
                            # Light debouncing for stability
                            if detected_motion == current_motion:
                                motion_count += 1
                            else:
                                motion_count -= 1
                                
                            # Change motion with minimal debouncing
                            if motion_count >= 3:  # Need 3 consistent readings
                                motion_count = 3
                            elif motion_count <= -3:  # Need 3 consistent different readings to change
                                if current_motion != detected_motion and detected_motion != "collecting_data":
                                    print(f"\n>>> MOTION CHANGED: {current_motion.upper()} -> {detected_motion.upper()}")
                                current_motion = detected_motion
                                motion_count = 0
                                
                            # Store data with recognized motion label
                            if current_motion != "collecting_data":
                                cursor.execute('''
                                INSERT INTO sensor_data 
                                (motion_label, accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z, sequence_id)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                                ''', (
                                    current_motion,
                                    accel_x, accel_y, accel_z,
                                    gyro_x, gyro_y, gyro_z,
                                    sequence_id
                                ))
                                
                                # Commit every 10 records
                                if cursor.rowcount % 10 == 0:
                                    conn.commit()
                            
                            # Print current motion status (throttled by time)
                            current_time = time.time()
                            if current_time - last_display_time >= display_interval:
                                print(f"Current motion: {current_motion.upper()}")
                                last_display_time = current_time
                            
                    except ValueError as e:
                        print(f"Error parsing data: {e} | Raw data: {line}")
                    except Exception as e:
                        print(f"Unexpected error: {e}")
                        
                time.sleep(0.01)  # Small delay to prevent CPU overload
                
        except KeyboardInterrupt:
            print("\nMotion recognition stopped by user.")
        finally:
            # Ensure final commit and cleanup
            conn.commit()
            ser.close()
            
    except mysql.connector.Error as e:
        print(f"Database error: {e}")
    except serial.SerialException as e:
        print(f"Serial port error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    read_and_recognize()