"""
Database models for the Walmart Employee Trust Score application.

This module defines the database schema with enhanced security features,
passkey support, and comprehensive activity tracking.
"""

from datetime import datetime, timezone, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from db import db
import secrets

class User(db.Model):
    """User model with enhanced security features."""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Passkey (FIDO2/WebAuthn) fields
    passkey_id = db.Column(db.String(64), unique=True, nullable=True)
    passkey_public_key = db.Column(db.Text, nullable=True)
    passkey_created_at = db.Column(db.DateTime, nullable=True)
    
    # Security fields
    failed_login_attempts = db.Column(db.Integer, default=0)
    account_locked_until = db.Column(db.DateTime, nullable=True)
    password_changed_at = db.Column(db.DateTime, nullable=True)
    
    # Trust score fields
    average_trust_score = db.Column(db.Float, default=0.0)
    total_logins = db.Column(db.Integer, default=0)
    
    # Relationships
    login_attempts = db.relationship('LoginAttempt', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, username, email, password, is_admin=False):
        """Initialize a new user with hashed password."""
        self.username = username
        self.email = email
        self.password_hash = generate_password_hash(password)
        self.is_admin = is_admin
        self.created_at = datetime.now(timezone.utc)
    
    def set_password(self, password):
        """Set a new password with hash."""
        self.password_hash = generate_password_hash(password)
        self.password_changed_at = datetime.now(timezone.utc)
    
    def check_password(self, password):
        """Check if the provided password matches the hash."""
        return check_password_hash(self.password_hash, password)
    
    def generate_passkey_id(self):
        """Generate a unique passkey identifier."""
        self.passkey_id = secrets.token_urlsafe(32)
        self.passkey_created_at = datetime.now(timezone.utc)
        return self.passkey_id
    
    def set_passkey(self, public_key):
        """Set the passkey public key."""
        self.passkey_public_key = public_key
        self.passkey_created_at = datetime.now(timezone.utc)
    
    def has_passkey(self):
        """Check if user has passkey configured."""
        return bool(self.passkey_id and self.passkey_public_key)
    
    def increment_failed_attempts(self):
        """Increment failed login attempts and potentially lock account."""
        self.failed_login_attempts += 1
        
        # Lock account after 5 failed attempts for 30 minutes
        if self.failed_login_attempts >= 5:
            self.account_locked_until = datetime.now(timezone.utc) + timedelta(minutes=30)
    
    def reset_failed_attempts(self):
        """Reset failed login attempts."""
        self.failed_login_attempts = 0
        self.account_locked_until = None
    
    def is_account_locked(self):
        """Check if account is currently locked."""
        if not self.account_locked_until:
            return False
        return datetime.now(timezone.utc) < self.account_locked_until
    
    def update_last_login(self):
        """Update last login timestamp."""
        self.last_login = datetime.now(timezone.utc)
        self.total_logins += 1
    
    def update_trust_score(self, new_score):
        """Update average trust score."""
        if self.total_logins == 0:
            self.average_trust_score = new_score
        else:
            # Weighted average (newer scores have more weight)
            self.average_trust_score = (self.average_trust_score * 0.7 + new_score * 0.3)
    
    def get_account_age_days(self):
        """Get account age in days."""
        return (datetime.now(timezone.utc) - self.created_at).days
    
    def to_dict(self):
        """Convert user to dictionary for API responses."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_admin': self.is_admin,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'has_passkey': self.has_passkey(),
            'average_trust_score': self.average_trust_score,
            'total_logins': self.total_logins,
            'account_age_days': self.get_account_age_days()
        }
    
    def __repr__(self):
        return f'<User {self.username}>'

class LoginAttempt(db.Model):
    """Enhanced login attempt tracking model."""
    
    __tablename__ = 'login_attempts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    
    # IP and location information
    ip_address = db.Column(db.String(45), nullable=False, index=True)
    user_agent = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(200), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    country = db.Column(db.String(100), nullable=True)
    region = db.Column(db.String(100), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    timezone = db.Column(db.String(50), nullable=True)
    isp = db.Column(db.String(200), nullable=True)
    
    # Trust score and security
    trust_score = db.Column(db.Float, nullable=False)
    is_suspicious = db.Column(db.Boolean, default=False, index=True)
    is_successful = db.Column(db.Boolean, default=False, index=True)
    failure_reason = db.Column(db.String(200), nullable=True)
    
    # Authentication method
    auth_method = db.Column(db.String(20), default='password')  # password, passkey, email_verification
    
    # Session information
    session_id = db.Column(db.String(64), nullable=True)
    device_fingerprint = db.Column(db.String(64), nullable=True)
    
    def __init__(self, user_id, ip_address, trust_score, **kwargs):
        """Initialize a new login attempt."""
        self.user_id = user_id
        self.ip_address = ip_address
        self.trust_score = trust_score
        self.timestamp = datetime.now(timezone.utc)
        
        # Set additional fields
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def mark_successful(self, session_id=None, device_fingerprint=None):
        """Mark this login attempt as successful."""
        self.is_successful = True
        self.session_id = session_id
        self.device_fingerprint = device_fingerprint
    
    def mark_failed(self, reason):
        """Mark this login attempt as failed."""
        self.is_successful = False
        self.failure_reason = reason
    
    def to_dict(self):
        """Convert login attempt to dictionary for API responses."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'ip_address': self.ip_address,
            'location': self.location,
            'city': self.city,
            'country': self.country,
            'trust_score': self.trust_score,
            'is_suspicious': self.is_suspicious,
            'is_successful': self.is_successful,
            'auth_method': self.auth_method,
            'failure_reason': self.failure_reason
        }
    
    def __repr__(self):
        return f'<LoginAttempt {self.id} - User {self.user_id}>'

class SecurityEvent(db.Model):
    """Security event logging for audit trail."""
    
    __tablename__ = 'security_events'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    
    # Event details
    event_type = db.Column(db.String(50), nullable=False, index=True)  # login_failed, suspicious_activity, etc.
    severity = db.Column(db.String(20), default='medium')  # low, medium, high, critical
    description = db.Column(db.Text, nullable=False)
    
    # Context information
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(200), nullable=True)
    
    # Additional data
    event_metadata = db.Column(db.Text, nullable=True)  # JSON string for additional data
    
    def __init__(self, event_type, description, user_id=None, severity='medium', **kwargs):
        """Initialize a new security event."""
        self.event_type = event_type
        self.description = description
        self.user_id = user_id
        self.severity = severity
        self.timestamp = datetime.now(timezone.utc)
        
        # Set additional fields
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def to_dict(self):
        """Convert security event to dictionary for API responses."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'event_type': self.event_type,
            'severity': self.severity,
            'description': self.description,
            'ip_address': self.ip_address,
            'location': self.location
        }
    
    def __repr__(self):
        return f'<SecurityEvent {self.event_type} - {self.timestamp}>' 