import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

def calculate_rms(values):
    """Calculate Root Mean Square of a list of values
    
    Args:
        values (list): List of numerical values
        
    Returns:
        float: RMS value
    """
    return np.sqrt(np.mean(np.square(values)))

def plot_time_series(timestamps, values, title="Time Series", ylabel="Value", color='b'):
    """Create a standardized time series plot
    
    Args:
        timestamps (list): List of time values
        values (list): List of corresponding values
        title (str): Plot title
        ylabel (str): Y-axis label
        color (str): Line color
        
    Returns:
        tuple: (fig, peaks_indices, valleys_indices)
    """
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(timestamps, values, f'{color}-', label=ylabel)
    
    # Find peaks and valleys
    values_array = np.array(values)
    peaks, _ = find_peaks(values_array)
    valleys, _ = find_peaks(-values_array)
    
    ax.plot(np.array(timestamps)[peaks], values_array[peaks], 'rx', label='Peaks')
    ax.plot(np.array(timestamps)[valleys], values_array[valleys], 'gx', label='Valleys')
    
    ax.set_title(title)
    ax.set_xlabel('Time')
    ax.set_ylabel(ylabel)
    ax.legend()
    ax.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    return fig, peaks, valleys

def save_matlab_data(filename, data_dict):
    """Save data in MATLAB .mat format
    
    Args:
        filename (str): Output file path
        data_dict (dict): Dictionary of data to save
    """
    from scipy.io import savemat
    savemat(filename, data_dict)
