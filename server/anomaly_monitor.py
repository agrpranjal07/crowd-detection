import numpy as np
from collections import deque
from sklearn.linear_model import LinearRegression

class AnomalyMonitor:
    def __init__(self):
        self.anomaly_scores = []
        self.anomaly_times = []
        self.rms_weight = 1.0
        self.crowd_weight = 1.0
        self.regressor = LinearRegression()
        self.score_window = deque(maxlen=30)

    def adaptive_weight(self, data):
        if len(data) < 10:
            return 1.0
        avg = np.mean(data)
        high = max(data[-5:])
        low = min(data[-5:])
        denom = (high + low)
        return 2 * avg / denom if denom != 0 else 1.0

    def update_anomaly_score(self, rms_list, crowd_list, rms_zscore, crowd_zscore, timestamp):
        self.rms_weight = self.adaptive_weight(rms_list)
        self.crowd_weight = self.adaptive_weight(crowd_list)
    
    # Ensure non-zero contribution from valid z-scores
        rms_contrib = self.rms_weight * max(rms_zscore, 0)  # No negative values
        crowd_contrib = self.crowd_weight * max(crowd_zscore, 0)
    
        total_score = rms_contrib + crowd_contrib
        self.anomaly_scores.append(total_score)
        self.anomaly_times.append(timestamp)
        self.score_window.append(total_score)

    # Dynamic threshold adjustment
        if len(self.score_window) >= 10:
            X = np.arange(len(self.score_window)).reshape(-1, 1)
            self.regressor.fit(X, self.score_window)
            baseline = self.regressor.predict([[len(self.score_window)]])[0]
            self.score_threshold = baseline * 1.5  # 50% above predicted trend

    def is_anomaly_detected(self):
        if len(self.anomaly_scores) < 10:
            return False
    # Check against dynamic threshold
        return self.anomaly_scores[-1] > self.score_threshold
