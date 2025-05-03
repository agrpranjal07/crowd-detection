import asyncio
import websockets
import cv2
import json

async def send_frames(video_path, server_uri):
    cap = cv2.VideoCapture(video_path)
    try:
        async with websockets.connect(server_uri) as websocket:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Encode frame as JPEG
                gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                _, buffer = cv2.imencode('.jpg', gray_frame)
                await websocket.send(buffer.tobytes())
                
                # Add small delay to prevent overwhelming server
                await asyncio.sleep(0.01)
            
            # Send end-of-stream signal
            await websocket.send(json.dumps({"status": "EOS"}))
            print("All frames sent")
    except websockets.exceptions.ConnectionClosed:
        print("Connection closed by server")

if __name__ == "__main__":
    VIDEO_PATH = "yt1z.net - Panic in Times Square after motorcycle backfire mistaken for gunfire (1080p).mp4"  # Update this path
    SERVER_URI = "ws://localhost:8765"
    
    # Use modern asyncio.run() instead of get_event_loop()
    asyncio.run(send_frames(VIDEO_PATH, SERVER_URI))