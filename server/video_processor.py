import cv2
from ultralytics import YOLO
from datetime import datetime
import numpy as np

class VideoProcessor:
    def __init__(self, model_path):
        """Base class for video processing with YOLOv8
        
        Args:
            model_path (str): Path to YOLOv8 model weights (.pt file)
        """
        self.model = YOLO(model_path)
        self.timestamps = []
        self.data = []
        self.frame_count = 0
        
    def process_frame(self, frame):
        """Process a single frame with YOLOv8
        
        Args:
            frame (np.array): Input frame in BGR format
            
        Returns:
            results: YOLOv8 detection results
        """
        results = self.model(frame, classes=[0], verbose=False)  # Only detect humans (class 0)
        return results
    
    def get_timestamp(self):
        """Generate formatted timestamp"""
        return datetime.now().strftime("%H:%M:%S.%f")[:-3]
    
    def resize_frame(self, frame, width=1280):
        """Maintain aspect ratio while resizing"""
        h, w = frame.shape[:2]
        height = int((width / w) * h)
        return cv2.resize(frame, (width, height))
