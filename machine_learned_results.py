import mysql.connector
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import os

# MySQL Database Configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'motion_app',
    'password': 'motion123',
    'database': 'motion_data'
}

class FixedPatternRecognizer:
    """Recognizes motion patterns with fixed motion breakdown visualization."""
    
    def __init__(self):
        # Time window for pattern analysis
        self.window_size = 15  # seconds
        
        # Hard-coded motion labels to match what's in your database
        self.motion_labels = ['resting', 'idle', 'walking', 'running']
        
        # Pattern definitions
        self.pattern_definitions = {
            'active': [
                {'motions': ['walking', 'running'], 'min_consecutive': 3, 'min_percentage': 0.4}
            ],
            'stationary': [
                {'motions': ['resting', 'idle'], 'min_consecutive': 5, 'min_percentage': 0.7}
            ],
            'mixed': [
                {'motions': ['walking', 'idle'], 'min_percentage': 0.4, 'min_transitions': 3}
            ]
        }
    
    def fetch_recent_data(self, minutes=60):
        """Fetch motion data from the last hour (or specified minutes)."""
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            # Calculate time range
            end_time = datetime.now()
            start_time = end_time - timedelta(minutes=minutes)
            
            print(f"Fetching data from {start_time} to {end_time}...")
            
            # Query to get recent data
            query = """
            SELECT timestamp, motion_label, accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z, sequence_id 
            FROM sensor_data
            WHERE timestamp >= %s
            ORDER BY timestamp ASC
            """
            
            cursor.execute(query, (start_time,))
            
            # Get column names
            columns = [i[0] for i in cursor.description]
            
            # Fetch all data
            data = cursor.fetchall()
            
            # Check for empty result
            if not data:
                print(f"No data found since {start_time}")
                
                # Check if there's any data at all
                cursor.execute("SELECT COUNT(*) FROM sensor_data")
                total_count = cursor.fetchone()[0]
                
                if total_count > 0:
                    # Get the most recent record timestamp
                    cursor.execute("SELECT MAX(timestamp) FROM sensor_data")
                    latest = cursor.fetchone()[0]
                    print(f"Total records in database: {total_count}")
                    print(f"Most recent record timestamp: {latest}")
                    print(f"Current time: {datetime.now()}")
                    
                    if latest:
                        time_diff = datetime.now() - latest
                        print(f"Data is {time_diff.total_seconds()/60:.1f} minutes old")
                        
                    # Check distribution of motion labels
                    cursor.execute("SELECT motion_label, COUNT(*) FROM sensor_data GROUP BY motion_label")
                    dist = cursor.fetchall()
                    print("Motion label distribution:")
                    for label, count in dist:
                        print(f"  {label}: {count} records")
                else:
                    print("No data found in the database at all.")
                
                # Create empty DataFrame
                df = pd.DataFrame(columns=columns)
            else:
                # Create DataFrame
                df = pd.DataFrame(data, columns=columns)
                
                # Convert timestamp to datetime
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                
                print(f"Found {len(df)} data points from the last {minutes} minutes.")
                
                # Check distribution of motion labels in this data
                label_counts = df['motion_label'].value_counts()
                print("Motion label distribution in recent data:")
                for label, count in label_counts.items():
                    print(f"  {label}: {count} records")
            
            # Close connection
            cursor.close()
            conn.close()
            
            return df
            
        except mysql.connector.Error as e:
            print(f"Database error: {e}")
            return pd.DataFrame()  # Return empty DataFrame on error
    
    def analyze_motion_segments(self, df):
        """Break the data into segments and analyze each segment."""
        if len(df) == 0:
            print("No data to analyze.")
            return pd.DataFrame()
            
        # Group data into time windows (15 second segments)
        df['time_window'] = pd.to_datetime(df['timestamp']).dt.floor(f"{self.window_size}S")
        windows = df.groupby('time_window')
        
        segments = []
        
        for window_name, window_data in windows:
            # Skip windows with too few data points
            if len(window_data) < 5:
                continue
            
            # Count each motion type
            motion_counts = window_data['motion_label'].value_counts()
            total_samples = len(window_data)
            
            # Calculate percentages
            motion_percentages = {}
            for motion in self.motion_labels:
                if motion in motion_counts:
                    motion_percentages[motion] = motion_counts[motion] / total_samples * 100
                else:
                    motion_percentages[motion] = 0
            
            # Find longest consecutive sequence for each motion
            motions = window_data['motion_label'].tolist()
            max_consecutive = {motion: 0 for motion in self.motion_labels}
            current_motion = None
            current_count = 0
            
            for motion in motions:
                if motion == current_motion:
                    current_count += 1
                else:
                    if current_motion is not None and current_motion in max_consecutive and current_count > max_consecutive[current_motion]:
                        max_consecutive[current_motion] = current_count
                    current_motion = motion
                    current_count = 1
            
            # Check last motion
            if current_motion is not None and current_motion in max_consecutive and current_count > max_consecutive[current_motion]:
                max_consecutive[current_motion] = current_count
            
            # Count transitions between different motions
            transitions = 0
            prev_motion = None
            
            for motion in motions:
                if prev_motion is not None and motion != prev_motion:
                    transitions += 1
                prev_motion = motion
            
            # Determine the pattern for this segment
            pattern = self.determine_pattern(motion_percentages, max_consecutive, transitions)
            
            # Store segment data
            segment = {
                'start_time': window_name,
                'end_time': window_name + timedelta(seconds=self.window_size),
                'resting_pct': motion_percentages.get('resting', 0),
                'idle_pct': motion_percentages.get('idle', 0),
                'walking_pct': motion_percentages.get('walking', 0),
                'running_pct': motion_percentages.get('running', 0),
                'max_consecutive_resting': max_consecutive.get('resting', 0),
                'max_consecutive_idle': max_consecutive.get('idle', 0),
                'max_consecutive_walking': max_consecutive.get('walking', 0),
                'max_consecutive_running': max_consecutive.get('running', 0),
                'transitions': transitions,
                'samples': total_samples,
                'pattern': pattern
            }
            
            segments.append(segment)
        
        # Create DataFrame of segments
        segments_df = pd.DataFrame(segments)
        
        if len(segments_df) == 0:
            print("No valid segments found in the data.")
        else:
            print(f"Created {len(segments_df)} segments.")
            
            # Check values in the first segment
            if len(segments_df) > 0:
                first_segment = segments_df.iloc[0]
                print("\nFirst segment details:")
                for col in ['resting_pct', 'idle_pct', 'walking_pct', 'running_pct']:
                    print(f"  {col}: {first_segment[col]:.2f}%")
        
        return segments_df
    
    def determine_pattern(self, percentages, max_consecutive, transitions):
        """Determine the pattern for a segment based on simple rules."""
        # Check each pattern definition
        for pattern_name, rules in self.pattern_definitions.items():
            for rule in rules:
                # Check if this rule matches
                rule_matches = True
                
                # Check motion percentages
                if 'min_percentage' in rule and rule['motions']:
                    total_pct = sum(percentages.get(m, 0) for m in rule['motions'])
                    if total_pct < rule['min_percentage'] * 100:
                        rule_matches = False
                
                # Check consecutive counts
                if 'min_consecutive' in rule and rule['motions']:
                    max_cons = max([max_consecutive.get(m, 0) for m in rule['motions']])
                    if max_cons < rule['min_consecutive']:
                        rule_matches = False
                
                # Check transitions
                if 'min_transitions' in rule and transitions < rule['min_transitions']:
                    rule_matches = False
                
                # If this rule matches, return the pattern
                if rule_matches:
                    return pattern_name
        
        # If no patterns match, return unknown
        return "unknown"
    
    def visualize_results(self, segments_df):
        """Create visualizations of the motion patterns."""
        if len(segments_df) == 0:
            print("No data to visualize.")
            return
        
        # Create a detailed summary of motion patterns
        print("\n===== MOTION PATTERN SUMMARY =====")
        pattern_counts = segments_df['pattern'].value_counts()
        for pattern, count in pattern_counts.items():
            print(f"{pattern}: {count} segments ({count/len(segments_df)*100:.1f}%)")
        
        # Print the 3 most recent segments in detail
        print("\n===== MOST RECENT SEGMENTS =====")
        recent_segments = segments_df.sort_values('end_time', ascending=False).head(3)
        
        for i, (_, segment) in enumerate(recent_segments.iterrows()):
            print(f"\nSegment {i+1} ({segment['start_time'].strftime('%H:%M:%S')} - {segment['end_time'].strftime('%H:%M:%S')}):")
            print(f"  Pattern: {segment['pattern']}")
            print(f"  Motion breakdown: {segment['resting_pct']:.1f}% resting, {segment['idle_pct']:.1f}% idle, " +
                  f"{segment['walking_pct']:.1f}% walking, {segment['running_pct']:.1f}% running")
            print(f"  Longest sequences: {segment['max_consecutive_resting']} resting, {segment['max_consecutive_idle']} idle, " +
                  f"{segment['max_consecutive_walking']} walking, {segment['max_consecutive_running']} running")
            print(f"  Motion transitions: {segment['transitions']}")
        
        # Create bar chart of motion percentages by time - FIXED VERSION
        plt.figure(figsize=(12, 6))
        
        # Sort by start time
        plot_df = segments_df.sort_values('start_time')
        
        # Create time labels
        time_labels = [t.strftime('%H:%M:%S') for t in plot_df['start_time']]
        
        # Debug information about the data being plotted
        print("\nDebug info for motion breakdown chart:")
        print(f"Number of time segments: {len(time_labels)}")
        
        # Check if there are any non-zero values
        has_data = False
        for motion in ['resting', 'idle', 'walking', 'running']:
            col = f"{motion}_pct"
            if col in plot_df.columns and plot_df[col].sum() > 0:
                has_data = True
                print(f"  {motion}: Sum={plot_df[col].sum():.1f}, Max={plot_df[col].max():.1f}%, Min={plot_df[col].min():.1f}%")
        
        if not has_data:
            print("Warning: No motion data found to plot!")
        
        # Create the stacked bar chart with explicit columns rather than dynamic lookup
        bar_width = 0.8
        bottom = np.zeros(len(plot_df))
        
        # Define motion colors
        motion_colors = {
            'resting': 'lightgray',
            'idle': 'darkgray',
            'walking': 'skyblue',
            'running': 'orange'
        }
        
        # Plot each motion type
        for motion, color in motion_colors.items():
            column = f"{motion}_pct"
            if column in plot_df.columns:
                # Convert percentage to proportion (0-1)
                values = plot_df[column].values / 100
                plt.bar(time_labels, values, bar_width, bottom=bottom, label=motion, color=color)
                bottom += values
        
        plt.xlabel('Time')
        plt.ylabel('Percentage')
        plt.title('Motion Breakdown by Time Segment')
        plt.legend(loc='upper right')
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Save the figure
        plt.savefig('motion_breakdown.png')
        print("\nSaved motion breakdown chart to 'motion_breakdown.png'")
        
        # Create pattern timeline
        plt.figure(figsize=(12, 3))
        
        # Create y-positions for each pattern
        pattern_types = sorted(segments_df['pattern'].unique())
        pattern_positions = {pattern: i for i, pattern in enumerate(pattern_types)}
        
        # Plot each segment as a horizontal line
        for _, segment in plot_df.iterrows():
            pattern = segment['pattern']
            start = segment['start_time']
            end = segment['end_time']
            y_pos = pattern_positions[pattern]
            
            plt.hlines(y=y_pos, xmin=start, xmax=end, 
                       linewidth=10, color=self.get_pattern_color(pattern))
        
        # Set y-ticks to pattern names
        plt.yticks(list(pattern_positions.values()), list(pattern_positions.keys()))
        
        plt.xlabel('Time')
        plt.title('Motion Patterns Timeline')
        plt.tight_layout()
        
        # Save the figure
        plt.savefig('pattern_timeline.png')
        print("Saved pattern timeline chart to 'pattern_timeline.png'")
        
        # Try to display the plots
        try:
            plt.show()
        except Exception as e:
            print(f"Unable to display plots: {e}")
            print("The images have been saved to files.")
    
    def get_pattern_color(self, pattern):
        """Return color for a given pattern."""
        colors = {
            'active': 'red',
            'stationary': 'blue',
            'mixed': 'green',
            'unknown': 'gray'
        }
        return colors.get(pattern, 'gray')

def main():
    """Main function to demonstrate pattern recognition with fixed visualization."""
    print("\n===== FIXED MOTION PATTERN RECOGNITION =====")
    print("This script analyzes recent motion data and identifies patterns")
    print("with an improved motion breakdown visualization.")
    
    # Create the recognizer
    recognizer = FixedPatternRecognizer()
    
    # Fetch recent data (last hour to increase chances of finding data)
    df = recognizer.fetch_recent_data(minutes=60)
    
    if len(df) > 0:
        # Analyze the data
        print("\nAnalyzing motion data into 15-second segments...")
        segments = recognizer.analyze_motion_segments(df)
        
        if len(segments) > 0:
            # Visualize the results
            recognizer.visualize_results(segments)
        else:
            print("\nNo valid segments found in the data.")
            print("Try running your motion detection script for a few minutes")
            print("while performing various activities to collect more data.")
    else:
        print("\nNo data found for analysis.")
        print("Make sure your motion detection script is running and collecting data.")
        print("Try the following troubleshooting steps:")
        print("1. Check that your Arduino and MPU6050 are properly connected")
        print("2. Verify that your motion detection script is running and correctly storing data")
        print("3. Confirm that the MySQL database connection is working")

if __name__ == "__main__":
    main()