import cv2
import numpy as np
from ultralytics import YOLO
import os
import time
import threading
from queue import Queue
import math
from collections import defaultdict
from data_bridge import DataBridgeClient

# Configuration
VIDEO_PATHS = [
    r"C:\Users\jayee\Downloads\ML model\1.mp4",  # North road
    r"C:\Users\jayee\Downloads\ML model\2.mp4",  # East road
    r"C:\Users\jayee\Downloads\ML model\3.mp4",  # South road
    r"C:\Users\jayee\Downloads\ML model\4.mp4"   # West road
]
OUTPUT_PATHS = [
    r"C:\Users\jayee\Downloads\ML model\north_output.mp4",  # North road output
    r"C:\Users\jayee\Downloads\ML model\east_output.mp4",   # East road output
    r"C:\Users\jayee\Downloads\ML model\south_output.mp4",  # South road output
    r"C:\Users\jayee\Downloads\ML model\west_output.mp4"    # West road output
]
ROAD_NAMES = ["North", "East", "South", "West"]
MIN_GREEN_TIME = 10  # Minimum green light time in seconds
MAX_GREEN_TIME = 60  # Maximum green light time in seconds
YELLOW_TIME = 3      # Yellow light duration in seconds
BASE_TIME = 20       # Base time for green light
UPDATE_INTERVAL = 5  # Update traffic signals every 5 seconds
CYCLE_TIME = 120     # Total cycle time in seconds (all 4 directions)

# Load YOLOv8 model once for all threads
print("Loading YOLO model...")
model = YOLO("yolov8n.pt")

# Vehicle class labels (from COCO dataset)
class_names = {2: 'Car', 3: 'Motorcycle', 5: 'Bus', 7: 'Truck'}

# Traffic data for each road
traffic_data = {
    road: {"active_vehicles": 0, "vehicle_counts": {2: 0, 3: 0, 5: 0, 7: 0}}
    for road in ROAD_NAMES
}

# Tracking parameters
conf_threshold = 0.3  # Minimum confidence for detection
iou_threshold = 0.5   # IOU threshold for considering same vehicle
track_timeout = 30    # Frames to keep tracking a vehicle after it disappears

# Traffic light states
current_green = 0  # Index of road with green light
traffic_state = ["RED", "RED", "RED", "RED"]
traffic_state[current_green] = "GREEN"
last_switch_time = time.time()

# Create data bridge client
data_bridge = DataBridgeClient()

# Class IDs for vehicles we want to detect
# 2: Car, 3: Motorcycle, 5: Bus, 7: Truck
CLASS_IDS = [2, 3, 5, 7]
CLASS_NAMES = {2: "Car", 3: "Motorcycle", 5: "Bus", 7: "Truck"}
CLASS_WEIGHTS = {2: 1.0, 3: 0.5, 5: 2.0, 7: 2.0}  # Weights for congestion calculation

# Vehicle tracking objects
active_vehicles = [{} for _ in range(len(ROAD_NAMES))]
vehicle_counts = [defaultdict(int) for _ in range(len(ROAD_NAMES))]
next_ids = [1 for _ in range(len(ROAD_NAMES))]

# Traffic signal states
LIGHT_STATES = ["RED", "YELLOW", "GREEN"]
current_state = ["RED", "RED", "RED", "RED"]

# Traffic cycle control
cycle_start_time = time.time()
cycle_elapsed = 0

# Green light time allocation for each road (will be dynamically adjusted)
green_times = {road_idx: MIN_GREEN_TIME for road_idx in range(len(ROAD_NAMES))}

# Initialize YOLO model
model = YOLO("yolov8n.pt")

# Locks for thread safety
vehicle_lock = threading.Lock()
signal_lock = threading.Lock()

# Helper function to calculate IoU (Intersection over Union)
def calculate_iou(box1, box2):
    # Box format: [x1, y1, x2, y2]
    x1_1, y1_1, x2_1, y2_1 = box1
    x1_2, y1_2, x2_2, y2_2 = box2
    
    # Calculate intersection area
    x_left = max(x1_1, x1_2)
    y_top = max(y1_1, y1_2)
    x_right = min(x2_1, x2_2)
    y_bottom = min(y2_1, y2_2)
    
    if x_right < x_left or y_bottom < y_top:
        return 0.0  # No intersection
    
    intersection_area = (x_right - x_left) * (y_bottom - y_top)
    
    # Calculate union area
    box1_area = (x2_1 - x1_1) * (y2_1 - y1_1)
    box2_area = (x2_2 - x1_2) * (y2_2 - y1_2)
    union_area = box1_area + box2_area - intersection_area
    
    return intersection_area / union_area if union_area > 0 else 0.0

# Calculate congestion level and determine optimal green time
def calculate_green_time(road_index, all_roads=False):
    """
    Calculate the optimal green light time for a road based on congestion
    If all_roads is True, calculate for all roads and return a dictionary
    """
    if all_roads:
        # Calculate congestion scores for all roads
        congestion_scores = {}
        for i, road in enumerate(ROAD_NAMES):
            data = traffic_data[road]
            
            # Calculate congestion score based on vehicle types
            congestion_scores[i] = (
                data["vehicle_counts"][2] * 1.0 +  # Cars
                data["vehicle_counts"][3] * 0.5 +  # Motorcycles
                data["vehicle_counts"][5] * 2.5 +  # Buses
                data["vehicle_counts"][7] * 2.0 +  # Trucks
                data["active_vehicles"] * 1.5      # Active vehicles have higher priority
            )
        
        # Calculate total congestion
        total_congestion = sum(congestion_scores.values())
        
        # Calculate proportional green times based on congestion
        green_times = {}
        available_time = CYCLE_TIME - (YELLOW_TIME * len(ROAD_NAMES))  # Subtract yellow light times
        
        for i in range(len(ROAD_NAMES)):
            if total_congestion > 0:
                # Proportional allocation based on congestion
                proportion = congestion_scores[i] / total_congestion
                green_times[i] = max(MIN_GREEN_TIME, int(proportion * available_time))
            else:
                # Equal distribution if no congestion data
                green_times[i] = available_time // len(ROAD_NAMES)
                
        # Adjust to ensure minimum green time and total cycle time
        total_assigned = sum(green_times.values()) + (YELLOW_TIME * len(ROAD_NAMES))
        
        # If we exceeded the cycle time, reduce proportionally
        if total_assigned > CYCLE_TIME:
            excess = total_assigned - CYCLE_TIME
            for i in range(len(ROAD_NAMES)):
                # Reduce proportionally but ensure minimum time
                green_times[i] = max(MIN_GREEN_TIME, green_times[i] - (excess * green_times[i] / available_time))
        
        return green_times
    else:
        # Original single road calculation
        road = ROAD_NAMES[road_index]
        data = traffic_data[road]
        
        # Calculate congestion score
        congestion_score = (
            data["vehicle_counts"][2] * 1.0 +  # Cars
            data["vehicle_counts"][3] * 0.5 +  # Motorcycles
            data["vehicle_counts"][5] * 2.5 +  # Buses
            data["vehicle_counts"][7] * 2.0    # Trucks
        )
        
        # Active vehicles have higher priority
        active_congestion = data["active_vehicles"] * 1.5
        
        # Calculate green time based on congestion
        green_time = BASE_TIME + min(MAX_GREEN_TIME - BASE_TIME, 
                                   math.sqrt(congestion_score + active_congestion))
        
        # Ensure green time is within limits
        green_time = max(MIN_GREEN_TIME, min(MAX_GREEN_TIME, green_time))
        
        return int(green_time)

# Function to process video from one road
def process_road_video(road_index, results_queue):
    road_name = ROAD_NAMES[road_index]
    video_path = VIDEO_PATHS[road_index]
    output_path = OUTPUT_PATHS[road_index]
    
    if not os.path.exists(video_path):
        print(f"Error: Video file not found at {video_path}")
        results_queue.put((road_index, False, f"Video file not found for {road_name} road"))
        return
    
    print(f"Processing {road_name} road video...")
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print(f"Error: Could not open video file for {road_name} road")
        results_queue.put((road_index, False, f"Could not open video for {road_name} road"))
        return
    
    # Get video properties
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_count = 0
    
    # Setup video writer for output
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))
    
    # Tracking data for this road
    tracked_vehicles = {}  # {id: (cls, box, last_seen_frame)}
    
    # Start processing frames
    start_time = time.time()
    last_report_time = start_time
    
    # Colors for different vehicle types
    colors = {
        2: (0, 255, 0),    # Cars: Green
        3: (0, 255, 255),  # Motorcycles: Yellow
        5: (255, 0, 0),    # Buses: Blue
        7: (0, 0, 255)     # Trucks: Red
    }
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            # Loop back to beginning of video
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue
        
        # Make a copy for visualization
        display_frame = frame.copy()
        
        # Run YOLOv8 detection
        results = model(frame, verbose=False)
        
        current_frame_vehicles = set()
        active_count = 0
        
        for r in results:
            for box in r.boxes:
                cls = int(box.cls[0])  # Class ID
                conf = float(box.conf[0])  # Confidence score
                
                if cls in [2, 3, 5, 7] and conf > conf_threshold:  # Vehicles only with good confidence
                    # Get coordinates
                    x1, y1, x2, y2 = map(float, box.xyxy[0])
                    box_coords = [x1, y1, x2, y2]
                    
                    # Convert to integers for drawing
                    x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
                    
                    # Calculate box center for better tracking
                    center_x = (x1 + x2) / 2
                    center_y = (y1 + y2) / 2
                    area = (x2 - x1) * (y2 - y1)
                    
                    # Check if this vehicle matches any tracked vehicle
                    matched = False
                    for vehicle_id, vehicle_info in list(tracked_vehicles.items()):
                        v_cls, v_box, v_last_frame = vehicle_info
                        
                        # Only match with same class
                        if cls != v_cls:
                            continue
                        
                        # Calculate IoU with tracked vehicle
                        iou = calculate_iou(box_coords, v_box)
                        
                        if iou > iou_threshold:
                            # Update the tracked vehicle's position
                            tracked_vehicles[vehicle_id] = (cls, box_coords, frame_count)
                            matched = True
                            current_frame_vehicles.add(vehicle_id)
                            active_count += 1
                            break
                    
                    # If not matched to existing vehicle, add as new
                    if not matched:
                        # Generate a unique ID
                        vehicle_id = f"{road_index}_{cls}_{int(center_x)}_{int(center_y)}_{int(area)}_{frame_count}"
                        tracked_vehicles[vehicle_id] = (cls, box_coords, frame_count)
                        current_frame_vehicles.add(vehicle_id)
                        active_count += 1
                        
                        # Update vehicle count for this road
                        traffic_data[road_name]["vehicle_counts"][cls] += 1
                    
                    # Draw vehicle bounding box and label
                    color = colors.get(cls, (255, 255, 255))  # Default to white if class not found
                    cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 2)
                    
                    # Add label with class name and confidence
                    label = f"{class_names[cls]} {conf:.2f}"
                    text_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
                    cv2.rectangle(display_frame, (x1, y1 - text_size[1] - 5), (x1 + text_size[0], y1), color, -1)
                    cv2.putText(display_frame, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
        
        # Update active vehicles count
        traffic_data[road_name]["active_vehicles"] = active_count
        
        # Remove vehicles that haven't been seen for a while
        for vehicle_id, (cls, box, last_seen) in list(tracked_vehicles.items()):
            if frame_count - last_seen > track_timeout:
                tracked_vehicles.pop(vehicle_id)
        
        # Add traffic signal status to the frame
        signal_color = (0, 0, 255)  # Default red
        if traffic_state[road_index] == "GREEN":
            signal_color = (0, 255, 0)  # Green
        elif traffic_state[road_index] == "YELLOW":
            signal_color = (0, 255, 255)  # Yellow
            
        # Add info box at the top of the frame
        cv2.rectangle(display_frame, (0, 0), (frame_width, 80), (0, 0, 0), -1)
        
        # Current traffic signal
        cv2.circle(display_frame, (30, 40), 15, signal_color, -1)
        
        # Road name and stats
        cv2.putText(display_frame, f"{road_name} Road", (60, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Vehicle counts
        vehicle_text = f"Active: {active_count} | Total: {sum(traffic_data[road_name]['vehicle_counts'].values())}"
        cv2.putText(display_frame, vehicle_text, (60, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Add counts by vehicle type on the right side
        type_text = f"Cars: {traffic_data[road_name]['vehicle_counts'][2]} | " + \
                    f"Buses: {traffic_data[road_name]['vehicle_counts'][5]} | " + \
                    f"Trucks: {traffic_data[road_name]['vehicle_counts'][7]}"
        cv2.putText(display_frame, type_text, (frame_width - 400, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Write frame to output video
        out.write(display_frame)
        
        # Report results periodically
        current_time = time.time()
        if current_time - last_report_time >= UPDATE_INTERVAL:
            results_queue.put((road_index, True, traffic_data[road_name]))
            last_report_time = current_time
        
        frame_count += 1
        
        # Small delay to reduce CPU usage
        time.sleep(0.01)
    
    # Clean up resources
    cap.release()
    out.release()
    
    results_queue.put((road_index, False, f"Video processing complete for {road_name} road. Output saved to {output_path}"))

# Function to control traffic signals
def traffic_signal_controller():
    global current_green, traffic_state, last_switch_time
    
    cycle_start_time = time.time()
    green_times = None
    
    while True:
        current_time = time.time()
        
        # Recalculate green times for all roads every cycle
        if green_times is None or (current_time - cycle_start_time >= CYCLE_TIME):
            green_times = calculate_green_time(None, all_roads=True)
            cycle_start_time = current_time
            
            # Log the calculated green times for this cycle
            times_str = ", ".join([f"{ROAD_NAMES[i]}: {green_times[i]:.1f}s" for i in range(len(ROAD_NAMES))])
            print(f"New cycle started - Green times: {times_str}")
        
        elapsed_time = current_time - last_switch_time
        
        # Get optimal green time for current road from the precalculated times
        optimal_green_time = green_times[current_green]
        
        # Check if it's time to switch the light
        if elapsed_time >= optimal_green_time:
            # Change current green to yellow
            traffic_state[current_green] = "YELLOW"
            print_traffic_status(f"Changing {ROAD_NAMES[current_green]} to YELLOW")
            
            # Wait for yellow time
            time.sleep(YELLOW_TIME)
            
            # Change to red
            traffic_state[current_green] = "RED"
            
            # Move to next road
            current_green = (current_green + 1) % len(ROAD_NAMES)
            
            # Set new road to green
            traffic_state[current_green] = "GREEN"
            last_switch_time = time.time()
            
            # Print the new traffic status
            next_green_time = green_times[current_green]
            print_traffic_status(f"Changing {ROAD_NAMES[current_green]} to GREEN for {next_green_time:.1f}s")
        
        # Sleep to avoid high CPU usage
        time.sleep(1)

# Print traffic status and congestion information
def print_traffic_status(message=""):
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print("\n====== SMART TRAFFIC CONTROL SYSTEM ======")
    if message:
        print(message)
    
    # Calculate cycle details
    total_cycle = CYCLE_TIME
    elapsed_cycle = (time.time() - cycle_start_time) % total_cycle
    remaining_cycle = total_cycle - elapsed_cycle
    
    print(f"\nCycle: {elapsed_cycle:.0f}s / {total_cycle}s ({remaining_cycle:.0f}s remaining)")
    print("\nCurrent Traffic Signal Status:")
    print("-" * 50)
    
    # Get green times for visual display
    green_times = calculate_green_time(None, all_roads=True)
    
    for i, road in enumerate(ROAD_NAMES):
        data = traffic_data[road]
        
        # Calculate congestion percentage
        total_vehicles = sum(data["vehicle_counts"].values())
        active = data["active_vehicles"]
        
        # Format for traffic light
        light_indicator = "🔴"
        if traffic_state[i] == "GREEN":
            light_indicator = "🟢"
        elif traffic_state[i] == "YELLOW":
            light_indicator = "🟡"
            
        # Calculate remaining time for green light
        time_info = ""
        if traffic_state[i] == "GREEN":
            elapsed = time.time() - last_switch_time
            remaining = max(0, green_times[i] - elapsed)
            time_info = f" - {remaining:.0f}s remaining"
        
        # Calculate congestion score for display
        congestion_score = (
            data["vehicle_counts"][2] * 1.0 +
            data["vehicle_counts"][3] * 0.5 +
            data["vehicle_counts"][5] * 2.5 +
            data["vehicle_counts"][7] * 2.0 +
            data["active_vehicles"] * 1.5
        )
        
        print(f"{light_indicator} {road} Road: {active} active, {total_vehicles} total vehicles{time_info}")
        print(f"   Cars: {data['vehicle_counts'][2]}, Motorcycles: {data['vehicle_counts'][3]}, " +
              f"Buses: {data['vehicle_counts'][5]}, Trucks: {data['vehicle_counts'][7]}")
        print(f"   Allocated green time: {green_times[i]:.1f}s | Congestion score: {congestion_score:.1f}")
    
    print("-" * 50)
    print("System running for: {:.1f} minutes".format((time.time() - system_start_time)/60))

# Main execution
if __name__ == "__main__":
    # Check if video files exist
    missing_videos = []
    for i, path in enumerate(VIDEO_PATHS):
        if not os.path.exists(path):
            missing_videos.append(ROAD_NAMES[i])
    
    if missing_videos:
        print(f"Warning: Missing video files for roads: {', '.join(missing_videos)}")
        print("Please check the file paths or provide demo videos.")
    
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(OUTPUT_PATHS[0])
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    print(f"\nOutput videos will be saved to:")
    for i, path in enumerate(OUTPUT_PATHS):
        print(f"  - {ROAD_NAMES[i]} Road: {path}")
    
    # Start the system
    system_start_time = time.time()
    cycle_start_time = system_start_time
    print("\nStarting Smart Traffic Control System...")
    
    # Create a queue for communication between threads
    results_queue = Queue()
    
    # Start video processing threads for each road
    threads = []
    for i in range(len(ROAD_NAMES)):
        thread = threading.Thread(target=process_road_video, args=(i, results_queue))
        thread.daemon = True
        thread.start()
        threads.append(thread)
    
    # Start traffic light controller in a separate thread
    controller_thread = threading.Thread(target=traffic_signal_controller)
    controller_thread.daemon = True
    controller_thread.start()
    
    # Main loop - process results from the queue and update display
    try:
        while True:
            # Check for updates from the road processing threads
            try:
                road_index, status, data = results_queue.get(timeout=1)
                if status:
                    # Update was successful with new traffic data
                    print_traffic_status()
                else:
                    # There was an error or notification
                    print(f"Message from {ROAD_NAMES[road_index]} road: {data}")
            except:
                # No updates in queue, just refresh the display
                print_traffic_status()
                time.sleep(1)
    
    except KeyboardInterrupt:
        print("\nStopping Smart Traffic Control System...")
    
    print("\nTraffic Control System Shutdown Complete.") 