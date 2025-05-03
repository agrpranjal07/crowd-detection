import pandas as pd
import matplotlib.pyplot as plt
from scipy.io import savemat
import os
import numpy as np

class DataSaver:
    def __init__(self, output_dir):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def save_data(self, density_data, velocity_data):
        """Save all data and plots"""
        # Save CSV files
        density_df = pd.DataFrame(density_data)
        velocity_df = pd.DataFrame(velocity_data)
        
        density_path = os.path.join(self.output_dir, "crowd_density.csv")
        velocity_path = os.path.join(self.output_dir, "velocity_data.csv")
        
        density_df.to_csv(density_path, index=False)
        velocity_df.to_csv(velocity_path, index=False)
        
        # Generate and save plots
        self.save_plots(density_data, velocity_data)
        
        return {
            "density_csv": density_path,
            "velocity_csv": velocity_path
        }
    
    def save_plots(self, density_data, velocity_data):
        """Generate and save visualization plots"""
        # Density Plots
        plt.figure(figsize=(12, 6))
        plt.subplot(1, 2, 1)
        plt.plot([d['timestamp'] for d in density_data], 
                [d['human_count'] for d in density_data], 'b-')
        plt.title("Human Count")
        plt.xticks(rotation=45)
        
        plt.subplot(1, 2, 2)
        plt.plot([d['timestamp'] for d in density_data], 
                [d['density_rate'] for d in density_data], 'r-')
        plt.title("Density Rate Change")
        plt.xticks(rotation=45)
        
        density_plot_path = os.path.join(self.output_dir, "density_analysis.jpg")
        plt.savefig(density_plot_path)
        plt.close()
        
        # Velocity Plots
        plt.figure(figsize=(12, 6))
        plt.subplot(1, 2, 1)
        plt.plot([v['timestamp'] for v in velocity_data], 
                [v['rms_velocity'] for v in velocity_data], 'g-')
        plt.title("RMS Velocity")
        plt.xticks(rotation=45)
        
        velocities = [v['rms_velocity'] for v in velocity_data]
        rates = np.diff(velocities) / np.diff(range(len(velocities)))
        plt.subplot(1, 2, 2)
        plt.plot([v['timestamp'] for v in velocity_data][1:], rates, 'm-')
        plt.title("Velocity Rate Change")
        plt.xticks(rotation=45)
        
        velocity_plot_path = os.path.join(self.output_dir, "velocity_analysis.jpg")
        plt.savefig(velocity_plot_path)
        plt.close()
        
        # Save MATLAB format
        savemat(os.path.join(self.output_dir, "analysis_data.mat"), {
            'density_data': density_data,
            'velocity_data': velocity_data,
            'density_plot_path': density_plot_path,
            'velocity_plot_path': velocity_plot_path
        })
