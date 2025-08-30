"""
Configuration settings for the Walmart Employee Trust Score application.

This module contains all configuration variables, environment-specific settings,
and security parameters for the application.
"""

import os
from datetime import timedelta

class Config:
    """Base configuration class with common settings."""
    
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///walmart.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Security Configuration
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    
    # Rate Limiting
    MAX_LOGIN_ATTEMPTS_PER_HOUR = 5
    MAX_API_REQUESTS_PER_MINUTE = 100
    
    # Trust Score Configuration
    TRUST_SCORE_THRESHOLD = 50  # Below this requires email verification
    SUSPICIOUS_SCORE_THRESHOLD = 30  # Below this blocks access
    GEO_DISTANCE_THRESHOLD_KM = 100  # Distance that triggers new location alert
    
    # Email Configuration
    EMAIL_API_URL = "https://api.emailjs.com/api/v1.0/email/send"
    EMAIL_SERVICE_ID = os.environ.get('EMAIL_SERVICE_ID') or "service_id"
    EMAIL_TEMPLATE_ID = os.environ.get('EMAIL_TEMPLATE_ID') or "template_id"
    EMAIL_USER_ID = os.environ.get('EMAIL_USER_ID') or "user_id"
    
    # IP Geolocation Configuration
    IP_GEO_API_URL = "https://ipapi.co/{ip}/json/"
    IP_GEO_TIMEOUT = 5  # seconds
    IP_GEO_FALLBACK_LOCATION = "Unknown"
    
    # Passkey Configuration (FIDO2/WebAuthn)
    PASSKEY_RP_NAME = "Walmart Employee Trust System"
    PASSKEY_RP_ID = os.environ.get('PASSKEY_RP_ID') or "localhost"
    PASSKEY_ORIGIN = os.environ.get('PASSKEY_ORIGIN') or "http://localhost:5000"
    
    # Logging Configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    LOG_FILE = os.environ.get('LOG_FILE') or 'walmart_trust.log'
    
    # Timezone Configuration
    DEFAULT_TIMEZONE = 'Asia/Calcutta'
    
    # Business Hours (for trust scoring)
    BUSINESS_HOURS_START = 9  # 9 AM
    BUSINESS_HOURS_END = 18   # 6 PM

class DevelopmentConfig(Config):
    """Development configuration with debug settings."""
    DEBUG = True
    SESSION_COOKIE_SECURE = False  # Allow HTTP in development
    SQLALCHEMY_TRACK_MODIFICATIONS = True

class ProductionConfig(Config):
    """Production configuration with strict security settings."""
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    
    @classmethod
    def init_app(cls, app):
        """Initialize production-specific settings."""
        # Check for required environment variables
        if not os.environ.get('SECRET_KEY'):
            raise ValueError("SECRET_KEY environment variable must be set in production")
        
        # Set SECRET_KEY from environment
        cls.SECRET_KEY = os.environ.get('SECRET_KEY')

class TestingConfig(Config):
    """Testing configuration with test database."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
} 
