"""
Unit tests for security features of the Walmart Employee Trust Score application.

This module tests:
- IP detection and geolocation
- Passkey authentication
- Rate limiting
- Session management
- Security event logging
"""

import unittest
from unittest.mock import patch, MagicMock, Mock
import time
import sys
import os
from datetime import datetime, timedelta, timezone
from flask import Flask, request
import json

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the modules to test
from utils.security import IPSecurity, PasskeyManager, RateLimiter, SessionManager
from utils.trust_calculator import TrustCalculator
from utils.email_service import EmailService

class TestIPSecurity(unittest.TestCase):
    """Test IP security and detection features."""
    
    def setUp(self):
        """Set up test environment."""
        self.app = Flask(__name__)
        self.app.config['IP_GEO_API_URL'] = "https://ipapi.co/{ip}/json/"
        self.app.config['IP_GEO_TIMEOUT'] = 5
        self.app.config['IP_GEO_FALLBACK_LOCATION'] = "Unknown"
        
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.request_context = self.app.test_request_context()
        self.request_context.push()
    
    def tearDown(self):
        """Clean up test environment."""
        self.request_context.pop()
        self.app_context.pop()
    
    def test_get_real_ip_address_cloudflare(self):
        """Test IP detection from Cloudflare header."""
        with self.app.test_request_context(headers={'CF-Connecting-IP': '192.168.1.100'}):
            ip = IPSecurity.get_real_ip_address()
            self.assertEqual(ip, '192.168.1.100')
    
    def test_get_real_ip_address_forwarded_for(self):
        """Test IP detection from X-Forwarded-For header."""
        with self.app.test_request_context(headers={'X-Forwarded-For': '203.0.113.1, 10.0.0.1'}):
            ip = IPSecurity.get_real_ip_address()
            self.assertEqual(ip, '203.0.113.1')
    
    def test_get_real_ip_address_fallback(self):
        """Test IP detection fallback to remote_addr."""
        with self.app.test_request_context():
            # Mock remote_addr
            with patch.object(request, 'remote_addr', '127.0.0.1'):
                ip = IPSecurity.get_real_ip_address()
                self.assertEqual(ip, '127.0.0.1')
    
    def test_is_valid_ip_valid(self):
        """Test valid IP address validation."""
        valid_ips = ['192.168.1.1', '10.0.0.1', '172.16.0.1', '8.8.8.8']
        for ip in valid_ips:
            self.assertTrue(IPSecurity._is_valid_ip(ip))
    
    def test_is_valid_ip_invalid(self):
        """Test invalid IP address validation."""
        invalid_ips = ['256.1.2.3', '1.2.3.256', '192.168.1', '192.168.1.1.1', '']
        for ip in invalid_ips:
            self.assertFalse(IPSecurity._is_valid_ip(ip))
    
    @patch('utils.security.requests.get')
    def test_get_ip_geolocation_success(self, mock_get):
        """Test successful IP geolocation."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'city': 'New York',
            'country_name': 'United States',
            'region': 'New York',
            'latitude': 40.7128,
            'longitude': -74.0060,
            'timezone': 'America/New_York',
            'org': 'Verizon'
        }
        mock_get.return_value = mock_response
        
        geo_info = IPSecurity.get_ip_geolocation('8.8.8.8')
        
        self.assertEqual(geo_info['city'], 'New York')
        self.assertEqual(geo_info['country'], 'United States')
        self.assertEqual(geo_info['latitude'], 40.7128)
        self.assertEqual(geo_info['longitude'], -74.0060)
    
    @patch('utils.security.requests.get')
    def test_get_ip_geolocation_api_error(self, mock_get):
        """Test IP geolocation with API error."""
        mock_response = Mock()
        mock_response.status_code = 429  # Rate limited
        mock_get.return_value = mock_response
        
        geo_info = IPSecurity.get_ip_geolocation('8.8.8.8')
        
        self.assertEqual(geo_info['city'], 'Unknown')
        self.assertEqual(geo_info['country'], 'Unknown')
        self.assertIsNone(geo_info['latitude'])
    
    @patch('utils.security.requests.get')
    def test_get_ip_geolocation_exception(self, mock_get):
        """Test IP geolocation with exception."""
        mock_get.side_effect = Exception("Network error")
        
        geo_info = IPSecurity.get_ip_geolocation('8.8.8.8')
        
        self.assertEqual(geo_info['city'], 'Unknown')
        self.assertEqual(geo_info['country'], 'Unknown')

class TestPasskeyManager(unittest.TestCase):
    """Test passkey authentication features."""
    
    def setUp(self):
        """Set up test environment."""
        self.app = Flask(__name__)
        self.app.config['PASSKEY_RP_ID'] = 'localhost'
        self.app.config['PASSKEY_RP_NAME'] = 'Test App'
        self.app.config['PASSKEY_ORIGIN'] = 'http://localhost:5000'
        
        self.app_context = self.app.app_context()
        self.app_context.push()
    
    def tearDown(self):
        """Clean up test environment."""
        self.app_context.pop()
    
    def test_generate_challenge(self):
        """Test passkey challenge generation."""
        challenge_data = PasskeyManager.generate_challenge()
        
        self.assertIn('challenge', challenge_data)
        self.assertIn('rpId', challenge_data)
        self.assertIn('rpName', challenge_data)
        self.assertEqual(challenge_data['rpId'], 'localhost')
        self.assertEqual(challenge_data['rpName'], 'Test App')
        self.assertEqual(challenge_data['userVerification'], 'preferred')
        self.assertEqual(challenge_data['timeout'], 60000)
    
    def test_verify_passkey_response_valid(self):
        """Test valid passkey response verification."""
        credential_data = {'id': 'test_credential_id'}
        user_id = 'test_user'
        
        result = PasskeyManager.verify_passkey_response(credential_data, user_id)
        self.assertTrue(result)
    
    def test_verify_passkey_response_invalid(self):
        """Test invalid passkey response verification."""
        credential_data = None
        user_id = 'test_user'
        
        result = PasskeyManager.verify_passkey_response(credential_data, user_id)
        self.assertFalse(result)
    
    def test_generate_passkey_id(self):
        """Test passkey ID generation."""
        passkey_id = PasskeyManager.generate_passkey_id()
        
        self.assertIsInstance(passkey_id, str)
        self.assertGreater(len(passkey_id), 0)

class TestRateLimiter(unittest.TestCase):
    """Test rate limiting functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.rate_limiter = RateLimiter()
    
    def test_rate_limiter_not_limited_initially(self):
        """Test that rate limiter allows initial attempts."""
        identifier = 'test_ip'
        result = self.rate_limiter.is_rate_limited(identifier, 5, 3600)
        self.assertFalse(result)
    
    def test_rate_limiter_limits_after_threshold(self):
        """Test that rate limiter blocks after threshold."""
        identifier = 'test_ip'
        
        # Make 5 attempts (should be allowed)
        for _ in range(5):
            result = self.rate_limiter.is_rate_limited(identifier, 5, 3600)
            self.assertFalse(result)
        
        # 6th attempt should be blocked
        result = self.rate_limiter.is_rate_limited(identifier, 5, 3600)
        self.assertTrue(result)
    
    def test_rate_limiter_resets_after_window(self):
        """Test that rate limiter resets after time window."""
        identifier = 'test_ip'
        
        # Make some attempts
        for _ in range(3):
            self.rate_limiter.is_rate_limited(identifier, 5, 1)  # 1 second window
        
        # Wait for window to expire
        time.sleep(1.1)
        
        # Should be allowed again
        result = self.rate_limiter.is_rate_limited(identifier, 5, 1)
        self.assertFalse(result)
    
    def test_get_remaining_attempts(self):
        """Test remaining attempts calculation."""
        identifier = 'test_ip'
        
        # Initially should have all attempts
        remaining = self.rate_limiter.get_remaining_attempts(identifier, 5, 3600)
        self.assertEqual(remaining, 5)
        
        # After one attempt
        self.rate_limiter.is_rate_limited(identifier, 5, 3600)
        remaining = self.rate_limiter.get_remaining_attempts(identifier, 5, 3600)
        self.assertEqual(remaining, 4)

class TestSessionManager(unittest.TestCase):
    """Test session management functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.app = Flask(__name__)
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.request_context = self.app.test_request_context()
        self.request_context.push()
    
    def tearDown(self):
        """Clean up test environment."""
        self.request_context.pop()
        self.app_context.pop()
    
    @patch('utils.security.IPSecurity.get_real_ip_address')
    def test_create_secure_session(self, mock_get_ip):
        """Test secure session creation."""
        mock_get_ip.return_value = '192.168.1.100'
        
        user_data = {
            'id': 1,
            'username': 'testuser',
            'is_admin': False
        }
        
        session_data = SessionManager.create_secure_session(user_data)
        
        self.assertEqual(session_data['user_id'], 1)
        self.assertEqual(session_data['username'], 'testuser')
        self.assertFalse(session_data['is_admin'])
        self.assertIn('session_id', session_data)
        self.assertIn('login_time', session_data)
        self.assertEqual(session_data['ip_address'], '192.168.1.100')
    
    def test_validate_session_valid(self):
        """Test valid session validation."""
        session_data = {
            'user_id': 1,
            'username': 'testuser',
            'login_time': datetime.now(timezone.utc).isoformat(),
            'session_id': 'test_session_id'
        }
        
        result = SessionManager.validate_session(session_data)
        self.assertTrue(result)
    
    def test_validate_session_invalid_missing_fields(self):
        """Test session validation with missing fields."""
        session_data = {
            'user_id': 1,
            'username': 'testuser'
            # Missing login_time and session_id
        }
        
        result = SessionManager.validate_session(session_data)
        self.assertFalse(result)
    
    def test_validate_session_expired(self):
        """Test session validation with expired session."""
        expired_time = datetime.now(timezone.utc) - timedelta(hours=9)
        session_data = {
            'user_id': 1,
            'username': 'testuser',
            'login_time': expired_time.isoformat(),
            'session_id': 'test_session_id'
        }
        
        result = SessionManager.validate_session(session_data)
        self.assertFalse(result)

class TestTrustCalculator(unittest.TestCase):
    """Test trust score calculation functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.app = Flask(__name__)
        self.app.config['BUSINESS_HOURS_START'] = 9
        self.app.config['BUSINESS_HOURS_END'] = 18
        self.app.config['GEO_DISTANCE_THRESHOLD_KM'] = 100
        
        self.app_context = self.app.app_context()
        self.app_context.push()
    
    def tearDown(self):
        """Clean up test environment."""
        self.app_context.pop()
    
    def test_calculate_haversine_distance(self):
        """Test haversine distance calculation."""
        # New York to Los Angeles (approximately 3935 km)
        distance = TrustCalculator.calculate_haversine_distance(
            40.7128, -74.0060, 34.0522, -118.2437
        )
        
        self.assertGreater(distance, 3900)
        self.assertLess(distance, 4000)
    
    def test_calculate_haversine_distance_same_location(self):
        """Test haversine distance for same location."""
        distance = TrustCalculator.calculate_haversine_distance(
            40.7128, -74.0060, 40.7128, -74.0060
        )
        
        self.assertAlmostEqual(distance, 0.0, places=1)
    
    def test_calculate_time_based_score_business_hours(self):
        """Test time-based score during business hours."""
        score = TrustCalculator.calculate_time_based_score(10, 1)  # 10 AM, Tuesday
        self.assertGreater(score, 100)  # Should have bonus for business hours
    
    def test_calculate_time_based_score_non_business_hours(self):
        """Test time-based score outside business hours."""
        score = TrustCalculator.calculate_time_based_score(22, 1)  # 10 PM, Tuesday
        self.assertLess(score, 100)  # Should have penalty for non-business hours
    
    def test_calculate_time_based_score_weekend(self):
        """Test time-based score on weekend."""
        score = TrustCalculator.calculate_time_based_score(10, 6)  # 10 AM, Sunday
        self.assertLess(score, 100)  # Should have penalty for weekend
    
    def test_calculate_location_based_score_same_location(self):
        """Test location-based score for same location."""
        score = TrustCalculator.calculate_location_based_score(0.0, 0.8)
        self.assertGreater(score, 100)  # Should have bonus for same location
    
    def test_calculate_location_based_score_different_country(self):
        """Test location-based score for different country."""
        score = TrustCalculator.calculate_location_based_score(5000.0, 0.2)
        self.assertLess(score, 100)  # Should have penalty for different country
    
    def test_calculate_behavior_based_score_perfect_record(self):
        """Test behavior-based score with perfect record."""
        score = TrustCalculator.calculate_behavior_based_score(0, 5, 365)
        self.assertGreater(score, 100)  # Should have bonus for perfect record
    
    def test_calculate_behavior_based_score_many_failures(self):
        """Test behavior-based score with many failures."""
        score = TrustCalculator.calculate_behavior_based_score(10, 100, 30)
        self.assertLess(score, 100)  # Should have penalty for many failures
    
    def test_calculate_composite_trust_score(self):
        """Test composite trust score calculation."""
        score = TrustCalculator.calculate_composite_trust_score(
            time_score=110.0,
            location_score=105.0,
            behavior_score=95.0,
            device_score=100.0
        )
        
        self.assertGreater(score, 0)
        self.assertLessEqual(score, 120)
    
    @patch('utils.trust_calculator.joblib.load')
    def test_ml_predict_trust_score_with_model(self, mock_load):
        """Test ML-based trust score prediction with model."""
        # Mock the ML model
        mock_model = Mock()
        mock_model.predict.return_value = [1]  # Normal behavior
        mock_model.decision_function.return_value = [0.2]  # Low anomaly score
        mock_load.return_value = mock_model
        
        trust_score, is_suspicious, require_passkey, new_location = TrustCalculator.ml_predict_trust_score(
            10, 50.0, 0, 5
        )
        
        self.assertGreater(trust_score, 0)
        self.assertLessEqual(trust_score, 100)
        self.assertIsInstance(is_suspicious, bool)
        self.assertIsInstance(require_passkey, bool)
        self.assertIsInstance(new_location, bool)
    
    def test_ml_predict_trust_score_fallback(self):
        """Test ML-based trust score prediction fallback."""
        trust_score, is_suspicious, require_passkey, new_location = TrustCalculator.ml_predict_trust_score(
            10, 50.0, 0, 5
        )
        
        self.assertGreater(trust_score, 0)
        self.assertLessEqual(trust_score, 100)
        self.assertIsInstance(is_suspicious, bool)
        self.assertIsInstance(require_passkey, bool)
        self.assertIsInstance(new_location, bool)

class TestEmailService(unittest.TestCase):
    """Test email service functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.app = Flask(__name__)
        self.app.config['EMAIL_API_URL'] = "https://api.emailjs.com/api/v1.0/email/send"
        self.app.config['EMAIL_SERVICE_ID'] = "test_service"
        self.app.config['EMAIL_TEMPLATE_ID'] = "test_template"
        self.app.config['EMAIL_USER_ID'] = "test_user"
        
        self.app_context = self.app.app_context()
        self.app_context.push()
    
    def tearDown(self):
        """Clean up test environment."""
        self.app_context.pop()
    
    @patch('utils.email_service.requests.post')
    def test_send_email_via_api_success(self, mock_post):
        """Test successful email sending via API."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        template_params = {
            'to_email': 'test@example.com',
            'subject': 'Test Subject',
            'message': 'Test Message'
        }
        
        result = EmailService.send_email_via_api(template_params)
        self.assertTrue(result)
    
    @patch('utils.email_service.requests.post')
    def test_send_email_via_api_failure(self, mock_post):
        """Test failed email sending via API."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response
        
        template_params = {
            'to_email': 'test@example.com',
            'subject': 'Test Subject',
            'message': 'Test Message'
        }
        
        result = EmailService.send_email_via_api(template_params)
        self.assertFalse(result)
    
    @patch('utils.email_service.requests.post')
    def test_send_security_alert(self, mock_post):
        """Test security alert email sending."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        result = EmailService.send_security_alert(
            'test@example.com', 'testuser', 'Suspicious Login',
            '192.168.1.100', 'New York, US'
        )
        self.assertTrue(result)
    
    @patch('utils.email_service.requests.post')
    def test_send_verification_code(self, mock_post):
        """Test verification code email sending."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        result = EmailService.send_verification_code(
            'test@example.com', 'testuser', '123456'
        )
        self.assertTrue(result)

if __name__ == '__main__':
    unittest.main() 