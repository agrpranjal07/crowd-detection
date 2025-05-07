import asyncio
import websockets
import cv2
import json

async def send_frames(video_path, server_uri):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video: {video_path}")
        print("Supported formats: ", [".mp4", ".avi", ".mov"])
        exit(1)
    try:
        async with websockets.connect(server_uri) as websocket:
            frame_count = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    print(f"End of video (sent {frame_count} frames)")
                    break
                
                # Reduce frame size and add compression
                frame = cv2.resize(frame, (640, 360))
                _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                
                try:
                    await websocket.send(buffer.tobytes())
                    frame_count += 1
                    # Wait for server acknowledgment
                    ack = await websocket.recv()
                    if json.loads(ack).get('status') != 'ACK':
                        break
                    await asyncio.sleep(0.03)  # Increased delay
                except websockets.exceptions.ConnectionClosed:
                    print("Server closed connection prematurely")
                    break
                
            await websocket.send(json.dumps({"status": "EOS"}))
    finally:
        cap.release()

if __name__ == "__main__":
    VIDEO_PATH = r"Crowd-Activity-All.mp4"  # Update path
    SERVER_URI = "ws://localhost:8765/client"  # Add /client endpoint
    
    asyncio.run(send_frames(VIDEO_PATH, SERVER_URI))