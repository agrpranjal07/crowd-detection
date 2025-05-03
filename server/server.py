import asyncio
import json
import base64
from datetime import datetime
import cv2
import numpy as np
import websockets
from websockets.exceptions import ConnectionClosed

from CrowdDensity import CrowdDensityAnalyzer
from RMSVelocity import VelocityAnalyzer
from DataSaver import DataSaver

MODEL_PATH = "yolov8n.pt"
OUTPUT_DIR = "analysis_results"

class ProcessingServer:
    def __init__(self, model_path: str, output_dir: str):
        self.density_analyzer = CrowdDensityAnalyzer(model_path)
        self.velocity_analyzer = VelocityAnalyzer(model_path)
        self.data_saver = DataSaver(output_dir)
        self.react_clients = set()
        self.frame_count = 0

    async def handle_processing_client(self, websocket):
        """Handle video processing client"""
        print(f"Processing client connected: {websocket.remote_address}")
        try:
            async for message in websocket:
                if isinstance(message, (bytes, bytearray)):
                    await self.process_frame(message)
        except ConnectionClosed as cc:
            print(f"Processing client disconnected: {cc.code} - {cc.reason}")
        except Exception as e:
            print(f"Processing error: {str(e)}")
        finally:
            await websocket.close()

    async def handle_react_client(self, websocket):
        """Handle dashboard clients"""
        print(f"React client connected: {websocket.remote_address}")
        self.react_clients.add(websocket)
        try:
            await websocket.wait_closed()
        except ConnectionClosed as cc:
            print(f"React client disconnected: {cc.code} - {cc.reason}")
        finally:
            self.react_clients.discard(websocket)

    async def process_frame(self, frame_data: bytes):
        """Process and broadcast frame"""
        try:
            # print(f"Processing frame {self.frame_count}")
            self.frame_count += 1
            
            # Decode and process frame
            frame = cv2.imdecode(np.frombuffer(frame_data, np.uint8), cv2.IMREAD_COLOR)
            if frame is None:
                raise ValueError("Invalid frame data received")

            # Run analytics
            density_results = self.density_analyzer.process_frame(frame)
            velocity_results = self.velocity_analyzer.process_frame(frame)

            # Save data
            self.data_saver.save_data(
                self.density_analyzer.data,
                self.velocity_analyzer.data
            )

            # Prepare broadcast message
            _, jpg_buf = cv2.imencode('.jpg', frame)
            msg = {
                "frame": base64.b64encode(jpg_buf).decode('utf-8'),
                "analytics": {
                    "count": len(density_results[0].boxes),
                    "density": self.density_analyzer.density_rates[-1],
                    "velocity": self.velocity_analyzer.velocities[-1],
                    "timestamp": datetime.now().isoformat()
                }
            }

            # Broadcast to React clients
            if self.react_clients:
                await asyncio.gather(*[
                    client.send(json.dumps(msg))
                    for client in self.react_clients
                ], return_exceptions=True)
            # print(f"Broadcasting to {len(self.react_clients)} clients")
            # print(f"Sample analytics: {msg['analytics']}")

        except Exception as e:
            print(f"Frame processing error: {str(e)}")

async def main():
    server = ProcessingServer(MODEL_PATH, OUTPUT_DIR)
    
    # Explicit IPv4 binding
    processing_server = await websockets.serve(
        server.handle_processing_client,
        '127.0.0.1',  # Use IPv4 explicitly
        8765,
        ping_interval=20,
        ping_timeout=60
    )
    
    react_server = await websockets.serve(
        server.handle_react_client,
        '127.0.0.1',  # Use IPv4 explicitly
        8766,
        ping_interval=20,
        ping_timeout=60
    )

    print("🟢 Processing: ws://127.0.0.1:8765")
    print("🟢 Dashboard:  ws://127.0.0.1:8766")
    await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🔴 Servers stopped gracefully")