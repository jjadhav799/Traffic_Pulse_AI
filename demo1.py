import cv2
import numpy as np
from ultralytics import YOLO
from collections import defaultdict
import os
import time

# Initialize YOLOv8 model
model = YOLO("yolov8n.pt")

# Open video feed - use absolute path
video_path = "D:/softwares/TrafficPulse AI/ml model/Test video.mp4"
print(f"Attempting to open video file: {video_path}")

# Check if the file exists
if not os.path.exists(video_path):
    print(f"Error: Video file not found at {video_path}")
    video_path = "Test video.mp4"  # Try relative path as fallback
    print(f"Trying relative path: {video_path}")

cap = cv2.VideoCapture(video_path)
if not cap.isOpened():
    print("Error: Could not open video file.")
    exit()

# Get video properties
frame_width = int(cap.get(3))
frame_height = int(cap.get(4))
fps = int(cap.get(cv2.CAP_PROP_FPS))

# Store previous object positions
object_positions = defaultdict(tuple)
next_object_id = 1

# Function to get current congestion level and vehicle count
def get_traffic_data():
    return congestion_level, vehicle_count

# Traffic congestion variables
vehicle_count = 0

seen_vehicle_ids = set()
start_time = time.time()
congestion_level = "LOW"
congestion_threshold = 15  # Number of vehicles to consider traffic as HIGH

# Traffic light control variables
green_light_time = 30  # Default green light duration in seconds
current_phase = "GREEN"  # Start with green phase
phase_start_time = time.time()

# Create a font for displaying congestion level
font = cv2.FONT_HERSHEY_SIMPLEX

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("Error: Could not read frame.")
        break

    results = model(frame)
    new_positions = {}

    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])  # Get bounding box
            conf = float(box.conf[0])  # Confidence score
            cls = int(box.cls[0])  # Class ID
            
            # Filter only vehicles (YOLO COCO classes: 2=car, 3=motorcycle, 5=bus, 7=truck)
            if cls in [2, 3, 5, 7] and conf > 0.5:
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2  # Calculate centroid
                
                # Assign object ID
                assigned_id = None
                for obj_id, (px, py) in object_positions.items():
                    if abs(cx - px) < 30 and abs(cy - py) < 30:  # Check if object is nearby
                        assigned_id = obj_id
                        break

                if assigned_id is None:
                    assigned_id = next_object_id
                    next_object_id += 1
                    
                    # Count only NEW vehicles
                    if assigned_id not in seen_vehicle_ids:
                        seen_vehicle_ids.add(assigned_id)
                        vehicle_count += 1

                new_positions[assigned_id] = (cx, cy)

                # Draw bounding box and ID
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"ID: {assigned_id}", (x1, y1 - 5), font, 0.5, (0, 255, 0), 2)

    object_positions = new_positions

    # Calculate congestion level every 10 seconds
    elapsed_time = time.time() - start_time
    if elapsed_time > 10:
        congestion_level = "HIGH" if vehicle_count > congestion_threshold else "LOW"
        print(f"Traffic Congestion: {congestion_level} (Vehicles in {elapsed_time:.1f} sec: {vehicle_count})")
        
        # Adjust traffic light timings based on congestion
        if congestion_level == "HIGH":
            green_light_time = 60  # Increase green light to 60 sec
        else:
            green_light_time = 30  # Reduce green light to 30 sec
            
        print(f"Setting green light duration to {green_light_time} seconds")
        
        # Reset count every 10 seconds
        vehicle_count = 0
        seen_vehicle_ids.clear()
        start_time = time.time()

    # Simulate traffic light phases
    phase_elapsed = time.time() - phase_start_time
    
    # Draw traffic light simulation
    if current_phase == "GREEN":
        light_color = (0, 255, 0)  # Green
        if phase_elapsed > green_light_time:
            current_phase = "YELLOW"
            phase_start_time = time.time()
    elif current_phase == "YELLOW":
        light_color = (0, 255, 255)  # Yellow
        if phase_elapsed > 5:  # Yellow phase is 5 seconds
            current_phase = "RED"
            phase_start_time = time.time()
    else:  # RED phase
        light_color = (0, 0, 255)  # Red
        if phase_elapsed > 40:  # Red phase is 40 seconds
            current_phase = "GREEN"
            phase_start_time = time.time()

    # Draw traffic light circle
    cv2.circle(frame, (frame_width - 50, 50), 30, light_color, -1)
    cv2.putText(frame, current_phase, (frame_width - 90, 100), font, 0.7, light_color, 2)
    
    # Display time remaining for current phase
    remaining_time = 0
    if current_phase == "GREEN":
        remaining_time = green_light_time - phase_elapsed
    elif current_phase == "YELLOW":
        remaining_time = 5 - phase_elapsed
    else:  # RED
        remaining_time = 40 - phase_elapsed
    
    cv2.putText(frame, f"Time: {int(remaining_time)}s", (frame_width - 90, 130), font, 0.7, light_color, 2)

    # Display congestion information on frame
    cv2.putText(frame, f"Congestion: {congestion_level}", (30, 30), font, 0.7, (0, 0, 255), 2)
    cv2.putText(frame, f"Vehicles: {vehicle_count}", (30, 60), font, 0.7, (0, 0, 255), 2)
    cv2.putText(frame, f"Time: {elapsed_time:.1f}s", (30, 90), font, 0.7, (0, 0, 255), 2)
    cv2.putText(frame, f"Green Light: {green_light_time}s", (30, 120), font, 0.7, (0, 0, 255), 2)

    # Show the video
    cv2.imshow("Traffic Tracking and Congestion Analysis", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
