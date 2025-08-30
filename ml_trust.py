from datetime import datetime
import numpy as np
try:
    from joblib import load
    model = load('trust_model.joblib')
except Exception:
    model = None

def calculate_trust_score(user, ip_address, timestamp, location, failed_attempts=0, api_rate=0, geo_distance=0):
    # Rule-based scoring for MVP
    score = 100
    hour = timestamp.hour
    # Penalize logins outside 9am-6pm
    if hour < 9 or hour > 18:
        score -= 30
    # Penalize high failed attempts
    if failed_attempts > 2:
        score -= 20
    # Penalize high API rate
    if api_rate > 100:
        score -= 20
    # Penalize new location (placeholder logic)
    if location == 'Unknown':
        score -= 20
    is_suspicious = score < 50
    new_location = geo_distance > 100
    return score, is_suspicious, new_location

def ml_predict_trust_score(hour, geo_distance, failed_attempts, api_rate):
    if model is None:
        # Fallback to rule-based with higher default score
        score = 85  # Higher default score to avoid email verification
        is_suspicious = False
        new_location = geo_distance > 100
        return score, is_suspicious, False, new_location
    
    X = np.array([[hour, geo_distance, failed_attempts, api_rate]])
    pred = model.predict(X)[0]  # -1: anomaly, 1: normal
    # Use anomaly score to create a trust score (0-100)
    anomaly_score = model.decision_function(X)[0]
    # Map anomaly_score to 0-100 (higher is better)
    trust_score = int(100 * (anomaly_score + 0.5))
    trust_score = max(0, min(100, trust_score))  # Ensure score is between 0-100
    
    # Boost trust score for normal behavior to avoid unnecessary email verification
    if pred == 1 and trust_score < 80:
        trust_score = min(100, trust_score + 20)  # Boost by 20 points for normal behavior
    
    is_suspicious = pred == -1 or trust_score < 50
    new_location = geo_distance > 100
    return trust_score, is_suspicious, False, new_location 