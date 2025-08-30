"""
API Endpoints for Browser Extension Integration
Provides RESTful API endpoints for the Walmart Trust Score Security browser extension.
"""

from flask import Flask, request, jsonify
from functools import wraps
import jwt
import datetime
from app import app, db
from models import User, LoginAttempt
from ml_trust import ml_predict_trust_score
import requests
from datetime import datetime, timedelta, timezone
from math import radians, sin, cos, sqrt, atan2
import pytz

# JWT Configuration
JWT_SECRET_KEY = 'walmart-trust-secret-key-change-in-production'
JWT_ALGORITHM = 'HS256'

def require_auth(f):
    """Decorator to require JWT authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({'error': 'No authorization header'}), 401
        
        try:
            # Extract token from "Bearer <token>"
            token = auth_header.split(' ')[1]
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            
            # Check if token is expired
            if datetime.fromtimestamp(payload['exp']) < datetime.now():
                return jsonify({'error': 'Token expired'}), 401
                
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        except Exception as e:
            return jsonify({'error': 'Authorization failed'}), 401
        
        return f(*args, **kwargs)
    return decorated

def generate_token():
    """Generate a JWT token for API access"""
    payload = {
        'exp': datetime.utcnow() + timedelta(hours=24),
        'iat': datetime.utcnow(),
        'sub': 'walmart-trust-api'
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

@app.route('/api/health', methods=['GET'])
def api_health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/api/auth/token', methods=['POST'])
def get_auth_token():
    """Get authentication token for API access"""
    try:
        # Simple token generation for demo
        # In production, this should validate credentials
        token = generate_token()
        return jsonify({
            'success': True,
            'token': token,
            'expires_in': 86400  # 24 hours
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/trust-score', methods=['POST'])
@require_auth
def calculate_trust_score():
    """Calculate trust score based on login metadata"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Extract metadata
        timestamp = data.get('timestamp')
        user_agent = data.get('userAgent', '')
        ip_address = data.get('ipAddress', '')
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        city = data.get('city', 'Unknown')
        country = data.get('country', 'Unknown')
        timezone = data.get('timezone', 'UTC')
        
        # Parse timestamp
        if timestamp:
            try:
                login_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except:
                login_time = datetime.now(timezone.utc)
        else:
            login_time = datetime.now(timezone.utc)
        
        # Calculate hour for trust scoring
        hour = login_time.hour
        
        # Calculate geo distance if coordinates available
        geo_distance = 0
        if latitude and longitude:
            # Get previous login location for comparison
            prev_attempt = LoginAttempt.query.order_by(LoginAttempt.timestamp.desc()).first()
            if prev_attempt and prev_attempt.latitude and prev_attempt.longitude:
                geo_distance = calculate_distance(
                    prev_attempt.latitude, prev_attempt.longitude,
                    latitude, longitude
                )
        
        # Calculate API rate (logins per hour)
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        api_rate = LoginAttempt.query.filter(
            LoginAttempt.timestamp >= one_hour_ago
        ).count()
        
        # Get failed attempts count
        failed_attempts = LoginAttempt.query.filter_by(is_suspicious=True).count()
        
        # Calculate trust score using ML model
        trust_score, is_suspicious, require_passkey, new_location = ml_predict_trust_score(
            hour, geo_distance, failed_attempts, api_rate
        )
        
        # Determine if email verification is required
        require_email_verification = trust_score < 50
        
        # Store the login attempt (without user_id for now)
        attempt = LoginAttempt(
            timestamp=login_time,
            ip_address=ip_address,
            user_agent=user_agent,
            location=f"{city}, {country}",
            city=city,
            country=country,
            latitude=latitude,
            longitude=longitude,
            trust_score=trust_score,
            is_suspicious=is_suspicious,
            is_successful=False  # Will be updated when user logs in
        )
        db.session.add(attempt)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'trust_score': trust_score,
            'is_suspicious': is_suspicious,
            'require_email_verification': require_email_verification,
            'new_location': new_location,
            'geo_distance_km': geo_distance,
            'api_rate': api_rate,
            'failed_attempts': failed_attempts,
            'location': f"{city}, {country}",
            'timestamp': login_time.isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/validate-login', methods=['POST'])
@require_auth
def validate_login():
    """Validate login credentials and return trust score"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        username = data.get('username')
        password = data.get('password')
        metadata = data.get('metadata', {})
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        
        # Find user
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            return jsonify({
                'success': False,
                'error': 'Invalid credentials'
            }), 401
        
        # Calculate trust score using metadata
        timestamp = metadata.get('timestamp')
        if timestamp:
            try:
                login_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except:
                login_time = datetime.now(timezone.utc)
        else:
            login_time = datetime.now(timezone.utc)
        
        hour = login_time.hour
        latitude = metadata.get('latitude')
        longitude = metadata.get('longitude')
        
        # Calculate geo distance
        geo_distance = 0
        if latitude and longitude:
            prev_attempt = LoginAttempt.query.filter_by(user_id=user.id).order_by(LoginAttempt.timestamp.desc()).first()
            if prev_attempt and prev_attempt.latitude and prev_attempt.longitude:
                geo_distance = calculate_distance(
                    prev_attempt.latitude, prev_attempt.longitude,
                    latitude, longitude
                )
        
        # Calculate rates
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        api_rate = LoginAttempt.query.filter(
            LoginAttempt.user_id == user.id,
            LoginAttempt.timestamp >= one_hour_ago
        ).count()
        
        failed_attempts = LoginAttempt.query.filter_by(user_id=user.id, is_suspicious=True).count()
        
        # Calculate trust score
        trust_score, is_suspicious, require_passkey, new_location = ml_predict_trust_score(
            hour, geo_distance, failed_attempts, api_rate
        )
        
        # Determine actions based on trust score
        require_email_verification = trust_score < 50
        block_login = is_suspicious and trust_score < 30
        
        # Store login attempt
        attempt = LoginAttempt(
            user_id=user.id,
            timestamp=login_time,
            ip_address=metadata.get('ipAddress', ''),
            user_agent=metadata.get('userAgent', ''),
            location=f"{metadata.get('city', 'Unknown')}, {metadata.get('country', 'Unknown')}",
            city=metadata.get('city'),
            country=metadata.get('country'),
            latitude=latitude,
            longitude=longitude,
            trust_score=trust_score,
            is_suspicious=is_suspicious,
            is_successful=not block_login
        )
        db.session.add(attempt)
        db.session.commit()
        
        if block_login:
            return jsonify({
                'success': False,
                'trust_score': trust_score,
                'is_suspicious': True,
                'require_email_verification': False,
                'message': 'Login blocked due to suspicious activity'
            })
        
        return jsonify({
            'success': True,
            'trust_score': trust_score,
            'is_suspicious': is_suspicious,
            'require_email_verification': require_email_verification,
            'message': 'Login validated successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/security-events', methods=['POST'])
@require_auth
def log_security_event():
    """Log security events from the extension"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        event_type = data.get('event_type')
        details = data.get('details', {})
        timestamp = data.get('timestamp')
        
        if not event_type:
            return jsonify({'error': 'Event type required'}), 400
        
        # Parse timestamp
        if timestamp:
            try:
                event_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except:
                event_time = datetime.now(timezone.utc)
        else:
            event_time = datetime.now(timezone.utc)
        
        # Create security event (you may need to add SecurityEvent model)
        # For now, we'll just log it
        print(f"SECURITY EVENT: {event_type} - {details} at {event_time}")
        
        return jsonify({
            'success': True,
            'event_logged': True
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points using Haversine formula"""
    R = 6371  # Earth's radius in kilometers
    
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    return R * c

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True) 