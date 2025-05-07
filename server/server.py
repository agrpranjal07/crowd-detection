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

# Initialize YOLO model
model = YOLO(r"yolov8n (1).pt")  # Added raw string for Windows path

# ... rest of your code remains the same ... # Update model path as needed

# Global variables for UI connections and processing state
ui_connections = set()
anomaly_monitor = AnomalyMonitor()
prev_centers = {}
crowd_history = deque(maxlen=100)
rms_history = deque(maxlen=100)
start_time = None

def calculate_velocity(prev, current):
    rms, cnt = 0, 0
    for i in current:
        if i in prev:
            dx = current[i][0] - prev[i][0]
            dy = current[i][1] - prev[i][1]
            rms += dx**2 + dy**2
            cnt += 1
    return (rms / cnt)**0.5 if cnt > 0 else 0

def check_anomaly(values, threshold=0.3, window_ratio=0.3):  # More sensitive defaults 1,0.2
    if len(values) <10: # Reduced minimum data requirement=5
        return 0.0
    window_size = max(1, int(len(values) * window_ratio))
    recent = values[-window_size:]
    historical = values[:-window_size] if len(values) > window_size else values
    
    avg_recent = np.mean(recent)
    avg_historical = np.mean(values) if values else 0
    std_dev = np.std(values) if len(values) > 1 else 1.0
    
    # Enhanced sensitivity for sparse data
    if std_dev < 1e-6:  # Handle near-zero variance
        return abs(avg_recent - avg_historical)
        
    return abs(avg_recent - avg_historical) / std_dev

async def process_frame(frame_bytes):
    global prev_centers, crowd_history, rms_history, start_time
    frame = cv2.imdecode(np.frombuffer(frame_bytes, np.uint8), cv2.IMREAD_COLOR)
    current_time = time.time() - start_time

    # YOLO detection
    results = model(frame)[0]
    if not results.boxes:
        print("No detections in frame")
        return b"", {}  # Return empty frame and analytics
    person_count = sum(int(box.cls[0]) == 0 for box in results.boxes)
    
    # Track movement
    current_centers = {}
    for i, box in enumerate(results.boxes):
        if int(box.cls[0]) == 0:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cx, cy = (x1+x2)//2, (y1+y2)//2
            current_centers[i] = (cx, cy)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)
    
    rms = calculate_velocity(prev_centers, current_centers) if prev_centers else 0
    prev_centers = current_centers.copy()

    # Anomaly detection
    # Replace boolean flags with z-scores
    crowd_zscore = check_anomaly([p[1] for p in crowd_history]) if crowd_history else 0.0
    rms_zscore = check_anomaly([v[1] for v in rms_history]) if rms_history else 0.0

    anomaly_monitor.update_anomaly_score(  # Call via class instance
    [v[1] for v in rms_history],
    [p[1] for p in crowd_history],
    rms_zscore,
    crowd_zscore,
    current_time
    )
# Inside process_frame():
    print(
    f"Anomaly Components: "
    f"CrowdZ={crowd_zscore:.2f}(w={anomaly_monitor.crowd_weight:.2f}) "
    f"RMSZ={rms_zscore:.2f}(w={anomaly_monitor.rms_weight:.2f}) "
    f"Total={anomaly_monitor.anomaly_scores[-1]:.2f} "
    #"Threshold={anomaly_monitor.score_threshold:.2f}"
    )
    # Update histories
    crowd_history.append((current_time, person_count))
    rms_history.append((current_time, rms))
    is_anomaly=1 if anomaly_monitor.is_anomaly_detected() else 0
    print(is_anomaly)

    # Encode frame
    _, buffer = cv2.imencode('.jpg', frame)
    return buffer.tobytes(), {
        'crowd': person_count,
        'velocity': rms,
        'anomaly': anomaly_monitor.anomaly_scores[-1] if anomaly_monitor.anomaly_scores else 0,
        'is_anomaly':is_anomaly,
        'timestamp': current_time
    }
    #print(current_time)

async def handle_connection(websocket, path):
    """Proper handler signature for websockets 10.x compatibility"""
    global start_time
    try:
        print(f"New connection: {path} from {websocket.remote_address}")
        
        if path == '/client':
            start_time = time.time()
            async for message in websocket:
                # Process frame and get analytics
                processed_frame, analytics = await process_frame(message)
                
                # Broadcast to all UI clients
                data = {
                    'frame': base64.b64encode(processed_frame).decode(),
                    'analytics': analytics
                }
                for conn in ui_connections.copy():
                    try:
                        await conn.send(json.dumps(data))
                    except:
                        ui_connections.remove(conn)
                
                # Send acknowledgment
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
    async with websockets.serve(
        handle_connection, 
        "0.0.0.0", 
        8765,
        ping_interval=20,
        ping_timeout=60
    ):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())