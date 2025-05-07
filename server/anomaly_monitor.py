import numpy as np
from collections import deque
from sklearn.linear_model import LinearRegression

class AnomalyMonitor:
    def __init__(self):
        self.anomaly_scores = []  # List to store anomaly scores over time
        self.anomaly_times = []  # Timestamps corresponding to each anomaly score
        self.rms_weight = 1.0  # Initial weight for RMS component
        self.crowd_weight = 1.0  # Initial weight for crowd component
        self.regressor = LinearRegression()  # Linear regression model for dynamic threshold
        self.score_window = deque(maxlen=30)  # Sliding window for recent scores

    def adaptive_weight(self, data):
        """Calculate adaptive weight based on recent data trends"""
        if len(data) < 10:
            return 1.0  # Default weight for insufficient data
        avg = np.mean(data)
        high = max(data[-5:])
        low = min(data[-5:])
        denom = (high + low)
        return 2 * avg / denom if denom != 0 else 1.0  # Prevent division by zero

    def update_anomaly_score(self, rms_list, crowd_list, rms_zscore, crowd_zscore, timestamp):
        """Update anomaly scores and weights based on current data"""
        self.rms_weight = self.adaptive_weight(rms_list)
        self.crowd_weight = self.adaptive_weight(crowd_list)

        # Calculate weighted scores for RMS and crowd components
        rms_score = self.rms_weight * rms_zscore
        crowd_score = self.crowd_weight * crowd_zscore

        total_score = rms_score + crowd_score  # Combine components for total anomaly score
        self.anomaly_scores.append(total_score)
        self.anomaly_times.append(timestamp)
        self.score_window.append(total_score)

        # Fit linear regression model for dynamic threshold adjustment
        if len(self.score_window) >= 10:
            X = np.arange(len(self.score_window)).reshape(-1, 1)
            Y = np.array(self.score_window)
            self.regressor.fit(X, Y)

    def is_anomaly_detected(self):
        """Determine if an anomaly has been detected based on recent scores"""
        if len(self.anomaly_scores) < 10:
            return False  # Insufficient data for anomaly detection

        # Compare recent average to overall average for anomaly detection
        portion = int(len(self.anomaly_scores) * 0.3)
        recent = self.anomaly_scores[-portion:]
        avg_recent = np.mean(recent)
        avg_total = np.mean(self.anomaly_scores)
        if avg_total == 0:
            return 0  # Prevent division by zero

        deviation = abs(avg_recent - avg_total) / avg_total  # Calculate deviation ratio
        print(f"Deviation: {deviation:.2f}, Recent Avg: {avg_recent:.2f}, Total Avg: {avg_total:.2f}")
        return 1 if deviation > 10 else 0  # Return anomaly status based on deviation threshold

