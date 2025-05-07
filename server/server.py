import asyncio
import websockets
import cv2
import json
import base64
import numpy as np
import time
from ultralytics import YOLO
from collections import deque
from anomaly_monitor import AnomalyMonitor

# Initialize YOLO model with a pre-trained weights file
model = YOLO(r"yolov8n (1).pt")  # Update model path as needed

# Global variables for managing UI connections and processing state
ui_connections = set()
anomaly_monitor = AnomalyMonitor()
prev_centers = {}  # Previous frame centers for velocity calculation
crowd_history = deque(maxlen=100)  # History of person counts
rms_history = deque(maxlen=100)  # History of RMS values
start_time = None  # Timestamp of when processing started

def calculate_velocity(prev, current):
    """Calculate the root mean square (RMS) velocity between previous and current positions"""
    rms, cnt = 0, 0
    for i in current:
        if i in prev:
            dx = current[i][0] - prev[i][0]
            dy = current[i][1] - prev[i][1]
            rms += dx**2 + dy**2
            cnt += 1
    return (rms / cnt)**0.5 if cnt > 0 else 0

def check_anomaly(values, threshold=0.5, window_ratio=0.3):
    """Check for anomalies based on recent and historical data deviation"""
    if len(values) < 10:
        return 0
    window_size = max(1, int(len(values) * window_ratio))
    recent = values[-window_size:]
    avg_recent = np.mean(recent)
    avg_historical = np.mean(values) if values else 0
    std_dev = np.std(values) if len(values) > 1 else 1.0   #calculation of standard deviation
    if std_dev == 0:
        return 0
    return 1 if abs(avg_recent - avg_historical) / std_dev > threshold else 0

async def process_frame(frame_bytes):
    """Process a single video frame for detecting objects and anomalies"""
    global prev_centers, crowd_history, rms_history, start_time
    frame = cv2.imdecode(np.frombuffer(frame_bytes, np.uint8), cv2.IMREAD_COLOR)
    current_time = time.time() - start_time

    # Perform object detection using YOLO model
    results = model(frame)[0]
    if not results.boxes:
        print("No detections in frame")
        return b"", {}  # Return empty frame and analytics if no detections
    person_count = sum(int(box.cls[0]) == 0 for box in results.boxes)  # Count detected humans

    # Track movement and calculate current centers
    current_centers = {}
    for i, box in enumerate(results.boxes):
        if int(box.cls[0]) == 0:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cx, cy = (x1+x2)//2, (y1+y2)//2
            current_centers[i] = (cx, cy)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

    # Calculate RMS velocity
    rms = calculate_velocity(prev_centers, current_centers) if prev_centers else 0
    prev_centers = current_centers.copy()

    # Detect anomalies based on crowd and velocity data
    crowd_zscore = check_anomaly([p[1] for p in crowd_history]) if crowd_history else 0.0
    rms_zscore = check_anomaly([v[1] for v in rms_history]) if rms_history else 0.0

    # Update anomaly scores with current data
    anomaly_monitor.update_anomaly_score(
        [v[1] for v in rms_history],
        [p[1] for p in crowd_history],
        rms_zscore,
        crowd_zscore,
        current_time
    )

    # Print anomaly components for debugging
    print(
        f"Anomaly Components: "
        f"CrowdZ={crowd_zscore:.2f}(w={anomaly_monitor.crowd_weight:.2f}) "
        f"RMSZ={rms_zscore:.2f}(w={anomaly_monitor.rms_weight:.2f}) "
        f"Total={anomaly_monitor.anomaly_scores[-1]:.2f}"
    )

    # Update history with current data
    crowd_history.append((current_time, person_count))
    rms_history.append((current_time, rms))
    anomaly_confidence = anomaly_monitor.is_anomaly_detected()
    is_anomaly = 1 if anomaly_monitor.anomaly_scores[-1] > 2.3 else 0
    print(is_anomaly)

    # Encode the processed frame for transmission
    _, buffer = cv2.imencode('.jpg', frame)
    return buffer.tobytes(), {
        'crowd': person_count,
        'velocity': rms,
        'anomaly': anomaly_monitor.anomaly_scores[-1] if anomaly_monitor.anomaly_scores else 0,
        'is_anomaly': is_anomaly,
        'timestamp': current_time
    }

async def handle_connection(websocket, path):
    """Handle incoming WebSocket connections"""
    global start_time
    try:
        print(f"New connection: {path} from {websocket.remote_address}")

        if path == '/client':
            start_time = time.time()
            async for message in websocket:
                # Process the incoming frame and obtain analytics
                processed_frame, analytics = await process_frame(message)

                # Broadcast processed frame and analytics to all connected UI clients
                data = {
                    'frame': base64.b64encode(processed_frame).decode(),
                    'analytics': analytics
                }
                for conn in ui_connections.copy():
                    try:
                        await conn.send(json.dumps(data))
                    except:
                        ui_connections.remove(conn)

                # Send acknowledgment back to the client
                await websocket.send(json.dumps({"status": "ACK"}))

        elif path == '/ui':
            ui_connections.add(websocket)
            await websocket.wait_closed()

    except websockets.exceptions.ConnectionClosedOK:
        print("Normal closure")
    except Exception as e:
        print(f"Connection error: {str(e)}")
    finally:
        ui_connections.discard(websocket)

async def main():
    """Main function to start the WebSocket server"""
    async with websockets.serve(
        handle_connection,
        "0.0.0.0",
        8765,
        ping_interval=20,
        ping_timeout=60
    ):
        await asyncio.Future()  # Run the server indefinitely

if __name__ == "__main__":
    asyncio.run(main())

