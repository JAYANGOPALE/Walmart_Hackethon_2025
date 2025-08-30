"""
Email service for the Walmart Employee Trust Score application.

This module provides email functionality using EmailJS API for:
- Verification codes
- Security alerts
- Welcome emails
- Password resets
"""

import requests
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from flask import current_app

logger = logging.getLogger(__name__)

class EmailService:
    """Email service using EmailJS API."""
    
    @staticmethod
    def send_email_via_api(template_params: Dict[str, Any], template_id: str = None) -> bool:
        """
        Send email via EmailJS API.
        
        Args:
            template_params: Parameters for the email template
            template_id: Email template ID (optional, uses default if not provided)
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            config = current_app.config
            
            if template_id is None:
                template_id = config['EMAIL_TEMPLATE_ID']
            
            payload = {
                "service_id": config['EMAIL_SERVICE_ID'],
                "template_id": template_id,
                "user_id": config['EMAIL_USER_ID'],
                "template_params": {
                    **template_params,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            }
            
            response = requests.post(
                config['EMAIL_API_URL'],
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Email sent successfully: {template_params.get('to_email', 'Unknown')}")
                return True
            else:
                logger.error(f"Email API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False
    
    @staticmethod
    def send_verification_code(email: str, username: str, code: str) -> bool:
        """
        Send verification code email.
        
        Args:
            email: Recipient email address
            username: Username for personalization
            code: Verification code
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        template_params = {
            "to_email": email,
            "to_name": username,
            "subject": "Walmart Trust System - Email Verification",
            "message": f"""
            Hello {username},
            
            Your verification code is: {code}
            
            This code will expire in 10 minutes. If you didn't request this code, 
            please contact support immediately.
            
            Best regards,
            Walmart Trust System Team
            """,
            "verification_code": code,
            "username": username
        }
        
        return EmailService.send_email_via_api(template_params)
    
    @staticmethod
    def send_security_alert(email: str, username: str, alert_type: str, 
                          ip_address: str, location: str) -> bool:
        """
        Send security alert email.
        
        Args:
            email: Recipient email address
            username: Username for personalization
            alert_type: Type of security alert
            ip_address: IP address of the suspicious activity
            location: Location of the suspicious activity
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        template_params = {
            "to_email": email,
            "to_name": username,
            "subject": "Walmart Trust System - Security Alert",
            "message": f"""
            Hello {username},
            
            We detected suspicious activity on your account:
            
            • Alert Type: {alert_type}
            • IP Address: {ip_address}
            • Location: {location}
            • Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
            
            If this was you, no action is required. If you don't recognize this activity,
            please change your password immediately and contact support.
            
            Best regards,
            Walmart Trust System Security Team
            """,
            "alert_type": alert_type,
            "ip_address": ip_address,
            "location": location,
            "username": username
        }
        
        return EmailService.send_email_via_api(template_params)
    
    @staticmethod
    def send_welcome_email(email: str, username: str) -> bool:
        """
        Send welcome email to new users.
        
        Args:
            email: Recipient email address
            username: Username for personalization
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        template_params = {
            "to_email": email,
            "to_name": username,
            "subject": "Welcome to Walmart Trust System",
            "message": f"""
            Hello {username},
            
            Welcome to the Walmart Employee Trust System!
            
            Your account has been successfully created. You can now log in to access
            the system and view your trust score.
            
            The trust system helps ensure secure access by monitoring login patterns
            and providing real-time security assessments.
            
            If you have any questions, please contact your system administrator.
            
            Best regards,
            Walmart Trust System Team
            """,
            "username": username
        }
        
        return EmailService.send_email_via_api(template_params)
    
    @staticmethod
    def send_password_reset(email: str, username: str, new_password: str) -> bool:
        """
        Send password reset email.
        
        Args:
            email: Recipient email address
            username: Username for personalization
            new_password: New temporary password
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        template_params = {
            "to_email": email,
            "to_name": username,
            "subject": "Walmart Trust System - Password Reset",
            "message": f"""
            Hello {username},
            
            Your password has been reset. Your new temporary password is:
            
            {new_password}
            
            Please log in with this password and change it immediately for security.
            
            If you didn't request this reset, please contact support immediately.
            
            Best regards,
            Walmart Trust System Team
            """,
            "username": username,
            "new_password": new_password
        }
        
        return EmailService.send_email_via_api(template_params)
    
    @staticmethod
    def send_login_notification(email: str, username: str, ip_address: str, 
                              location: str, trust_score: float) -> bool:
        """
        Send login notification email.
        
        Args:
            email: Recipient email address
            username: Username for personalization
            ip_address: IP address of the login
            location: Location of the login
            trust_score: Trust score for this login
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        template_params = {
            "to_email": email,
            "to_name": username,
            "subject": "Walmart Trust System - Login Notification",
            "message": f"""
            Hello {username},
            
            A new login was detected on your account:
            
            • IP Address: {ip_address}
            • Location: {location}
            • Trust Score: {trust_score}/100
            • Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
            
            If this was you, no action is required. If you don't recognize this login,
            please contact support immediately.
            
            Best regards,
            Walmart Trust System Team
            """,
            "username": username,
            "ip_address": ip_address,
            "location": location,
            "trust_score": str(trust_score)
        }
        
        return EmailService.send_email_via_api(template_params)
    
    @staticmethod
    def send_account_locked_notification(email: str, username: str, 
                                       reason: str, unlock_time: str) -> bool:
        """
        Send account locked notification email.
        
        Args:
            email: Recipient email address
            username: Username for personalization
            reason: Reason for account lock
            unlock_time: When the account will be unlocked
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        template_params = {
            "to_email": email,
            "to_name": username,
            "subject": "Walmart Trust System - Account Locked",
            "message": f"""
            Hello {username},
            
            Your account has been temporarily locked due to security concerns:
            
            • Reason: {reason}
            • Unlock Time: {unlock_time}
            
            This is a security measure to protect your account. The lock will be
            automatically removed at the specified time.
            
            If you believe this is an error, please contact support.
            
            Best regards,
            Walmart Trust System Security Team
            """,
            "username": username,
            "reason": reason,
            "unlock_time": unlock_time
        }
        
        return EmailService.send_email_via_api(template_params) 