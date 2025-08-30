"""
Trust score calculator for the Walmart Employee Trust Score application.

This module provides advanced trust score calculation algorithms based on:
- Login patterns and timing
- Geographic location analysis
- Device and IP consistency
- Historical behavior analysis
- Machine learning predictions
"""

import numpy as np
import logging
from datetime import datetime, timedelta
from typing import Tuple, Optional, Dict, Any
from math import radians, sin, cos, sqrt, atan2
from flask import current_app

logger = logging.getLogger(__name__)

class TrustCalculator:
    """Advanced trust score calculator with multiple algorithms."""
    
    @staticmethod
    def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate the great circle distance between two points on Earth.
        
        Args:
            lat1, lon1: Latitude and longitude of first point
            lat2, lon2: Latitude and longitude of second point
            
        Returns:
            float: Distance in kilometers
        """
        if not all(isinstance(x, (int, float)) for x in [lat1, lon1, lat2, lon2]):
            return 0.0
        
        try:
            R = 6371  # Earth's radius in kilometers
            
            # Convert to radians
            lat1_rad = radians(lat1)
            lon1_rad = radians(lon1)
            lat2_rad = radians(lat2)
            lon2_rad = radians(lon2)
            
            # Differences
            dlat = lat2_rad - lat1_rad
            dlon = lon2_rad - lon1_rad
            
            # Haversine formula
            a = sin(dlat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon/2)**2
            c = 2 * atan2(sqrt(a), sqrt(1-a))
            
            distance = R * c
            return round(distance, 2)
            
        except Exception as e:
            logger.error(f"Error calculating haversine distance: {e}")
            return 0.0
    
    @staticmethod
    def calculate_time_based_score(hour: int, day_of_week: int) -> float:
        """
        Calculate trust score based on login time patterns.
        
        Args:
            hour: Hour of day (0-23)
            day_of_week: Day of week (0=Monday, 6=Sunday)
            
        Returns:
            float: Time-based trust score (0-120)
        """
        config = current_app.config
        business_start = config['BUSINESS_HOURS_START']
        business_end = config['BUSINESS_HOURS_END']
        
        # Base score
        score = 100.0
        
        # Business hours bonus
        if business_start <= hour <= business_end:
            score += 20
        else:
            # Penalty for non-business hours
            if hour < 6 or hour > 22:  # Late night/early morning
                score -= 40
            else:
                score -= 20
        
        # Weekend penalty
        if day_of_week >= 5:  # Saturday (5) or Sunday (6)
            score -= 15
        
        # Specific time patterns
        if hour == 0:  # Midnight
            score -= 50
        elif 1 <= hour <= 5:  # Very early morning
            score -= 30
        
        return max(0, min(120, score))
    
    @staticmethod
    def calculate_location_based_score(geo_distance: float, location_consistency: float) -> float:
        """
        Calculate trust score based on location patterns.
        
        Args:
            geo_distance: Distance from previous login location in km
            location_consistency: Historical location consistency score (0-1)
            
        Returns:
            float: Location-based trust score (0-120)
        """
        score = 100.0
        
        # Distance-based scoring
        if geo_distance == 0:
            score += 20  # Same location bonus
        elif geo_distance <= 10:
            score += 10  # Nearby location
        elif geo_distance <= 50:
            score += 5   # Same city/region
        elif geo_distance <= 100:
            score -= 10  # Different city
        elif geo_distance <= 500:
            score -= 30  # Different state/province
        else:
            score -= 50  # Different country/continent
        
        # Location consistency bonus
        consistency_bonus = location_consistency * 20
        score += consistency_bonus
        
        return max(0, min(120, score))
    
    @staticmethod
    def calculate_behavior_based_score(failed_attempts: int, api_rate: int, 
                                     account_age_days: int) -> float:
        """
        Calculate trust score based on user behavior patterns.
        
        Args:
            failed_attempts: Number of failed login attempts
            api_rate: API requests per minute
            account_age_days: Account age in days
            
        Returns:
            float: Behavior-based trust score (0-120)
        """
        score = 100.0
        
        # Failed attempts penalty
        if failed_attempts == 0:
            score += 15  # Perfect record bonus
        elif failed_attempts <= 2:
            score -= 10
        elif failed_attempts <= 5:
            score -= 25
        else:
            score -= 50
        
        # API rate penalty
        if api_rate <= 10:
            score += 10  # Normal usage
        elif api_rate <= 50:
            score -= 5   # High usage
        elif api_rate <= 100:
            score -= 15  # Very high usage
        else:
            score -= 30  # Excessive usage
        
        # Account age bonus
        if account_age_days >= 365:  # 1+ year
            score += 20
        elif account_age_days >= 90:  # 3+ months
            score += 10
        elif account_age_days >= 30:  # 1+ month
            score += 5
        
        return max(0, min(120, score))
    
    @staticmethod
    def calculate_device_based_score(ip_address: str, user_agent: str, 
                                   known_devices: list) -> float:
        """
        Calculate trust score based on device and IP consistency.
        
        Args:
            ip_address: Current IP address
            user_agent: Browser/device user agent
            known_devices: List of known device signatures
            
        Returns:
            float: Device-based trust score (0-100)
        """
        score = 100.0
        
        # IP consistency check
        if ip_address in known_devices:
            score += 25  # Known IP
        else:
            score -= 20  # Unknown IP
        
        # User agent consistency
        user_agent_hash = hash(user_agent) % 1000
        if user_agent_hash in known_devices:
            score += 15  # Known device
        else:
            score -= 10  # Unknown device
        
        # IP range analysis (simplified)
        try:
            ip_parts = ip_address.split('.')
            if len(ip_parts) == 4:
                # Check if IP is in corporate range (example)
                if ip_parts[0] == '10' or (ip_parts[0] == '192' and ip_parts[1] == '168'):
                    score += 10  # Internal network
                elif ip_parts[0] == '172' and 16 <= int(ip_parts[1]) <= 31:
                    score += 10  # Internal network
        except (ValueError, IndexError):
            pass
        
        return max(0, min(100, score))
    
    @staticmethod
    def calculate_composite_trust_score(
        time_score: float,
        location_score: float,
        behavior_score: float,
        device_score: float,
        weights: Optional[Dict[str, float]] = None
    ) -> float:
        """
        Calculate composite trust score using weighted average.
        
        Args:
            time_score: Time-based trust score
            location_score: Location-based trust score
            behavior_score: Behavior-based trust score
            device_score: Device-based trust score
            weights: Optional custom weights for each component
            
        Returns:
            float: Composite trust score (0-100)
        """
        if weights is None:
            weights = {
                'time': 0.25,
                'location': 0.30,
                'behavior': 0.25,
                'device': 0.20
            }
        
        # Normalize weights
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v/total_weight for k, v in weights.items()}
        
        # Calculate weighted average
        composite_score = (
            time_score * weights['time'] +
            location_score * weights['location'] +
            behavior_score * weights['behavior'] +
            device_score * weights['device']
        )
        
        return round(max(0, min(100, composite_score)), 2)
    
    @staticmethod
    def ml_predict_trust_score(hour: int, geo_distance: float, failed_attempts: int, 
                              api_rate: int) -> Tuple[float, bool, bool, bool]:
        """
        Machine learning-based trust score prediction.
        
        Args:
            hour: Hour of day
            geo_distance: Geographic distance from previous login
            failed_attempts: Number of failed attempts
            api_rate: API requests per minute
            
        Returns:
            Tuple of (trust_score, is_suspicious, require_passkey, new_location)
        """
        try:
            # Try to load the ML model
            from joblib import load
            model = load('trust_model.joblib')
            
            # Prepare features
            X = np.array([[hour, geo_distance, failed_attempts, api_rate]])
            
            # Get prediction and anomaly score
            prediction = model.predict(X)[0]  # -1: anomaly, 1: normal
            anomaly_score = model.decision_function(X)[0]
            
            # Map anomaly score to trust score (0-100)
            # Higher anomaly score = lower trust score
            trust_score = int(100 * (1 - (anomaly_score + 0.5)))
            trust_score = max(0, min(100, trust_score))
            
            # Boost trust score for normal behavior
            if prediction == 1 and trust_score < 80:
                trust_score = min(100, trust_score + 20)
            
            # Determine flags
            is_suspicious = prediction == -1 or trust_score < 50
            require_passkey = trust_score < 30  # Very low trust requires passkey
            new_location = geo_distance > current_app.config['GEO_DISTANCE_THRESHOLD_KM']
            
            logger.info(f"ML prediction: score={trust_score}, suspicious={is_suspicious}, "
                       f"passkey={require_passkey}, new_location={new_location}")
            
            return trust_score, is_suspicious, require_passkey, new_location
            
        except Exception as e:
            logger.warning(f"ML model failed, using fallback: {e}")
            return TrustCalculator._fallback_trust_score(hour, geo_distance, failed_attempts, api_rate)
    
    @staticmethod
    def _fallback_trust_score(hour: int, geo_distance: float, failed_attempts: int, 
                             api_rate: int) -> Tuple[float, bool, bool, bool]:
        """
        Fallback trust score calculation when ML model is unavailable.
        
        Args:
            hour: Hour of day
            geo_distance: Geographic distance from previous login
            failed_attempts: Number of failed attempts
            api_rate: API requests per minute
            
        Returns:
            Tuple of (trust_score, is_suspicious, require_passkey, new_location)
        """
        # Calculate individual component scores
        time_score = TrustCalculator.calculate_time_based_score(hour, datetime.now().weekday())
        location_score = TrustCalculator.calculate_location_based_score(geo_distance, 0.5)
        behavior_score = TrustCalculator.calculate_behavior_based_score(failed_attempts, api_rate, 30)
        device_score = 85.0  # Default device score
        
        # Calculate composite score
        trust_score = TrustCalculator.calculate_composite_trust_score(
            time_score, location_score, behavior_score, device_score
        )
        
        # Determine flags
        is_suspicious = trust_score < 50
        require_passkey = trust_score < 30
        new_location = geo_distance > current_app.config['GEO_DISTANCE_THRESHOLD_KM']
        
        logger.info(f"Fallback calculation: score={trust_score}, suspicious={is_suspicious}, "
                   f"passkey={require_passkey}, new_location={new_location}")
        
        return trust_score, is_suspicious, require_passkey, new_location 