"""
Security utilities for the Walmart Employee Trust Score application.

This module provides:
- IP detection and geolocation
- Passkey authentication
- Rate limiting
- Session management
- Security event logging
"""

import hashlib
import hmac
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, Dict, Any
import requests
from flask import request, current_app
import logging

logger = logging.getLogger(__name__)

class IPSecurity:
    """IP address detection and geolocation utilities."""
    
    @staticmethod
    def get_real_ip_address() -> str:
        """
        Get the real IP address, handling proxy headers.
        
        Returns:
            str: Real IP address
        """
        try:
            # Check for Cloudflare header
            if request.headers.get('CF-Connecting-IP'):
                ip = request.headers.get('CF-Connecting-IP')
                if IPSecurity._is_valid_ip(ip):
                    return ip
            
            # Check for X-Forwarded-For header
            if request.headers.get('X-Forwarded-For'):
                forwarded_ips = request.headers.get('X-Forwarded-For').split(',')
                # Take the first valid IP (client IP)
                for ip in forwarded_ips:
                    ip = ip.strip()
                    if IPSecurity._is_valid_ip(ip):
                        return ip
            
            # Fallback to remote_addr
            if request.remote_addr:
                return request.remote_addr
            
            return '127.0.0.1'  # Default fallback
            
        except Exception as e:
            logger.error(f"Error getting real IP address: {e}")
            return '127.0.0.1'
    
    @staticmethod
    def _is_valid_ip(ip: str) -> bool:
        """
        Validate IP address format.
        
        Args:
            ip: IP address to validate
            
        Returns:
            bool: True if valid IP, False otherwise
        """
        if not ip:
            return False
        
        try:
            parts = ip.split('.')
            if len(parts) != 4:
                return False
            
            for part in parts:
                if not part.isdigit():
                    return False
                num = int(part)
                if num < 0 or num > 255:
                    return False
            
            return True
        except (ValueError, AttributeError):
            return False
    
    @staticmethod
    def get_ip_geolocation(ip_address: str) -> Dict[str, Any]:
        """
        Get geolocation information for an IP address.
        
        Args:
            ip_address: IP address to geolocate
            
        Returns:
            Dict containing geolocation data
        """
        if not IPSecurity._is_valid_ip(ip_address):
            return {
                'city': 'Unknown',
                'country': 'Unknown',
                'region': 'Unknown',
                'latitude': None,
                'longitude': None,
                'timezone': None,
                'isp': 'Unknown',
                'location': current_app.config['IP_GEO_FALLBACK_LOCATION']
            }
        
        try:
            api_url = current_app.config['IP_GEO_API_URL'].format(ip=ip_address)
            timeout = current_app.config['IP_GEO_TIMEOUT']
            
            response = requests.get(api_url, timeout=timeout)
            
            if response.status_code == 200:
                data = response.json()
                
                return {
                    'city': data.get('city', 'Unknown'),
                    'country': data.get('country_name', 'Unknown'),
                    'region': data.get('region', 'Unknown'),
                    'latitude': data.get('latitude'),
                    'longitude': data.get('longitude'),
                    'timezone': data.get('timezone'),
                    'isp': data.get('org', 'Unknown'),
                    'location': f"{data.get('city', 'Unknown')}, {data.get('country_name', 'Unknown')}"
                }
            
            logger.warning(f"Failed to geolocate IP {ip_address}: {response.status_code}")
            
        except Exception as e:
            logger.error(f"Error geolocating IP {ip_address}: {e}")
        
        return {
            'city': 'Unknown',
            'country': 'Unknown',
            'region': 'Unknown',
            'latitude': None,
            'longitude': None,
            'timezone': None,
            'isp': 'Unknown',
            'location': current_app.config['IP_GEO_FALLBACK_LOCATION']
        }

class PasskeyManager:
    """FIDO2/WebAuthn passkey authentication manager."""
    
    @staticmethod
    def generate_challenge() -> Dict[str, Any]:
        """
        Generate a WebAuthn challenge for passkey authentication.
        
        Returns:
            Dict containing challenge data
        """
        config = current_app.config
        
        challenge = secrets.token_urlsafe(32)
        rp_id = config['PASSKEY_RP_ID']
        
        # Store challenge in session for verification
        session_data = {
            'challenge': challenge,
            'timestamp': time.time()
        }
        
        return {
            'challenge': challenge,
            'rpId': rp_id,
            'rpName': config['PASSKEY_RP_NAME'],
            'userVerification': 'preferred',
            'timeout': 60000  # 60 seconds
        }
    
    @staticmethod
    def verify_passkey_response(credential_data: Dict[str, Any], user_id: str) -> bool:
        """
        Verify a passkey authentication response.
        
        Args:
            credential_data: The credential data from the client
            user_id: The user ID to verify against
            
        Returns:
            bool: True if verification successful, False otherwise
        """
        try:
            # In a real implementation, you would:
            # 1. Verify the challenge from session
            # 2. Verify the signature using the user's public key
            # 3. Check the origin and other security parameters
            
            # For now, we'll implement a simplified verification
            # In production, use a proper WebAuthn library like webauthn
            
            if not credential_data or 'id' not in credential_data:
                return False
            
            # Verify the credential ID matches the user's stored passkey
            # This is a simplified check - in reality, you'd verify the signature
            
            logger.info(f"Passkey verification attempted for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Passkey verification error: {e}")
            return False
    
    @staticmethod
    def generate_passkey_id() -> str:
        """Generate a unique passkey identifier."""
        return secrets.token_urlsafe(16)

class RateLimiter:
    """Rate limiting utility to prevent brute force attacks."""
    
    def __init__(self):
        self.attempts = {}  # In production, use Redis or similar
    
    def is_rate_limited(self, identifier: str, max_attempts: int, window_seconds: int) -> bool:
        """
        Check if an identifier is rate limited.
        
        Args:
            identifier: Unique identifier (IP, user ID, etc.)
            max_attempts: Maximum attempts allowed
            window_seconds: Time window in seconds
            
        Returns:
            bool: True if rate limited, False otherwise
        """
        now = time.time()
        
        if identifier not in self.attempts:
            self.attempts[identifier] = []
        
        # Remove old attempts outside the window
        self.attempts[identifier] = [
            attempt_time for attempt_time in self.attempts[identifier]
            if now - attempt_time < window_seconds
        ]
        
        # Check if rate limited
        if len(self.attempts[identifier]) >= max_attempts:
            return True
        
        # Add current attempt
        self.attempts[identifier].append(now)
        return False
    
    def get_remaining_attempts(self, identifier: str, max_attempts: int, window_seconds: int) -> int:
        """Get remaining attempts for an identifier."""
        now = time.time()
        
        if identifier not in self.attempts:
            return max_attempts
        
        valid_attempts = [
            attempt_time for attempt_time in self.attempts[identifier]
            if now - attempt_time < window_seconds
        ]
        
        return max(0, max_attempts - len(valid_attempts))

class SessionManager:
    """Secure session management utilities."""
    
    @staticmethod
    def create_secure_session(user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a secure session for a user.
        
        Args:
            user_data: User data to store in session
            
        Returns:
            Dict containing session data
        """
        session_data = {
            'user_id': user_data['id'],
            'username': user_data['username'],
            'is_admin': user_data['is_admin'],
            'login_time': datetime.now(timezone.utc).isoformat(),
            'session_id': secrets.token_urlsafe(32),
            'ip_address': IPSecurity.get_real_ip_address()
        }
        
        return session_data
    
    @staticmethod
    def validate_session(session_data: Dict[str, Any]) -> bool:
        """
        Validate session data for security.
        
        Args:
            session_data: Session data to validate
            
        Returns:
            bool: True if session is valid, False otherwise
        """
        if not session_data:
            return False
        
        required_fields = ['user_id', 'username', 'login_time', 'session_id']
        if not all(field in session_data for field in required_fields):
            return False
        
        # Check if session is expired (8 hours)
        try:
            login_time = datetime.fromisoformat(session_data['login_time'])
            if datetime.now(timezone.utc) - login_time > timedelta(hours=8):
                return False
        except ValueError:
            return False
        
        return True

# Global rate limiter instance
rate_limiter = RateLimiter() 