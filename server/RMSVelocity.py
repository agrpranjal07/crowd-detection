from video_processor import VideoProcessor
import numpy as np
import matplotlib.pyplot as plt

class VelocityAnalyzer(VideoProcessor):
    def __init__(self, model_path):
        super().__init__(model_path)
        self.velocities = []
        self.prev_positions = {}
        self.frame_count = 0
        
    def calculate_velocity(self, current_positions):
        """Calculate RMS velocity"""
        velocities = []
        for id, pos in current_positions.items():
            if id in self.prev_positions:
                dx = pos[0] - self.prev_positions[id][0]
                dy = pos[1] - self.prev_positions[id][1]
                velocities.append(np.sqrt(dx**2 + dy**2))
        self.prev_positions = current_positions
        return np.sqrt(np.mean([v**2 for v in velocities])) if velocities else 0
    
    def process_frame(self, frame):
        results = super().process_frame(frame)
        current_positions = {}
        
        for i, box in enumerate(results[0].boxes):
            current_positions[i] = (float(box.xywh[0][0]), float(box.xywh[0][1]))
        
        rms_velocity = self.calculate_velocity(current_positions)
        self.velocities.append(rms_velocity)
        self.timestamps.append(self.get_timestamp())
        self.frame_count += 1
        
        self.data.append({
            "timestamp": self.timestamps[-1],
            "rms_velocity": rms_velocity
        })
        
        return results
    
    def generate_plots(self):
        """Generate velocity analysis plots"""
        plt.figure(figsize=(12, 6))
        
        # RMS Velocity Plot
        plt.subplot(1, 2, 1)
        plt.plot(self.timestamps, self.velocities, 'g-')
        plt.title("RMS Velocity Over Time")
        plt.xlabel("Time")
        plt.ylabel("Velocity (pixels/frame)")
        plt.xticks(rotation=45)
        
        # Rate of Change Plot
        rates = np.diff(self.velocities) / np.diff(range(len(self.velocities)))
        plt.subplot(1, 2, 2)
        plt.plot(self.timestamps[1:], rates, 'm-')
        plt.title("Velocity Rate Change")
        plt.xlabel("Time")
        plt.ylabel("Acceleration Rate")
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        return plt
