import numpy as np
import cv2
from ultralytics import YOLO
import time
from collections import deque

def initialize_parameters():
    model_path = "yolov8s(1).pt"
    video_path = r"../client/Crowd-Activity-All.mp4"
    return model_path, video_path

def calculate_velocity(prev_centers, current_centers):
    rms = 0
    cnt = 0
    for i in current_centers:
        if i in prev_centers:
            dx = current_centers[i][0] - prev_centers[i][0]
            dy = current_centers[i][1] - prev_centers[i][1]
            rms += dx**2 + dy**2
            cnt += 1
    return (rms / cnt)**0.5 if cnt > 0 else 0

def check_anomaly(values, threshold=0.3, window_ratio=0.3):
    if len(values) < 10:
        return False
    window_size = max(1, int(len(values) * window_ratio))
    recent = values[-window_size:]
    avg_recent = np.mean(recent)
    full_avg = np.mean(values)
    std_dev = np.std(values) if len(values) > 1 else 0
    if std_dev == 0:
        return False
    z_score = abs(avg_recent - full_avg) / std_dev
    return z_score > threshold