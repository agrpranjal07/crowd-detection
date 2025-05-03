from video_processor import VideoProcessor
import numpy as np
import matplotlib.pyplot as plt

class CrowdDensityAnalyzer(VideoProcessor):
    def __init__(self, model_path):
        super().__init__(model_path)
        self.human_counts = []
        self.density_rates = []
        
    def calculate_density_rate(self):
        """Calculate rate of change of crowd density"""
        if len(self.human_counts) > 1:
            rate = (self.human_counts[-1] - self.human_counts[-2]) / (len(self.human_counts) * 1.0)
            self.density_rates.append(rate)
        else:
            self.density_rates.append(0)
    
    def process_frame(self, frame):
        results = super().process_frame(frame)
        human_count = len(results[0].boxes)
        
        self.human_counts.append(human_count)
        self.timestamps.append(self.get_timestamp())
        self.calculate_density_rate()
        
        # Real-time plotting data
        self.data.append({
            "timestamp": self.timestamps[-1],
            "human_count": human_count,
            "density_rate": self.density_rates[-1]
        })
        
        return results
    
    def generate_plots(self):
        """Generate density analysis plots"""
        plt.figure(figsize=(12, 6))
        
        # Human Count Plot
        plt.subplot(1, 2, 1)
        plt.plot(self.timestamps, self.human_counts, 'b-')
        plt.title("Human Count Over Time")
        plt.xlabel("Time")
        plt.ylabel("Number of Humans")
        plt.xticks(rotation=45)
        
        # Density Rate Plot
        plt.subplot(1, 2, 2)
        plt.plot(self.timestamps, self.density_rates, 'r-')
        plt.title("Crowd Density Rate Change")
        plt.xlabel("Time")
        plt.ylabel("Rate of Change")
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        return plt
