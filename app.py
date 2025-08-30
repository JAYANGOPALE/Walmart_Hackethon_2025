from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from db import db
from ml_trust import ml_predict_trust_score
import smtplib
from datetime import datetime, timedelta, timezone
import socket
import requests
from math import radians, sin, cos, sqrt, atan2
import random
import string
import pytz
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///walmart.db'
db.init_app(app)
app.secret_key = 'supersecretkey'  # Needed for session

with app.app_context():
    from models import User, LoginAttempt

# Email API configuration
EMAIL_API_URL = "https://api.emailjs.com/api/v1.0/email/send"
EMAIL_SERVICE_ID = "service_id"  # Replace with your EmailJS service ID
EMAIL_TEMPLATE_ID = "template_id"  # Replace with your EmailJS template ID
EMAIL_USER_ID = "user_id"  # Replace with your EmailJS user ID

def send_email_via_api(to_email, subject, message):
    """Send email using EmailJS API (free tier available)"""
    try:
        payload = {
            "service_id": EMAIL_SERVICE_ID,
            "template_id": EMAIL_TEMPLATE_ID,
            "user_id": EMAIL_USER_ID,
            "template_params": {
                "to_email": to_email,
                "subject": subject,
                "message": message
            }
        }
        
        response = requests.post(EMAIL_API_URL, json=payload)
        if response.status_code == 200:
            print(f"Email sent successfully to {to_email}")
            return True
        else:
            print(f"Email API error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Email sending failed: {e}")
        return False

# Helper: send email alert
def send_alert_email(to_email, username, reason):
    subject = "Walmart Security Alert - Suspicious Login"
    message = f"""
    Hello {username},
    
    A suspicious login attempt was detected for your account.
    
    Reason: {reason}
    Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    
    If this was not you, please contact support immediately.
    
    Best regards,
    Walmart Security Team
    """
    
    # Try API first, fallback to console
    if not send_email_via_api(to_email, subject, message):
        print(f"ALERT: Email to {to_email} - Suspicious login for {username}: {reason}")

# Helper: send email verification code
def send_verification_email(to_email, username, code):
    subject = "Walmart - Email Verification Code"
    message = f"""
    Hello {username},
    
    Your email verification code is: {code}
    
    Please enter this code to complete your login.
    
    This code will expire in 10 minutes.
    
    Best regards,
    Walmart Security Team
    """
    
    # Try API first, fallback to console
    if not send_email_via_api(to_email, subject, message):
        print(f"VERIFICATION CODE: Email to {to_email} - Verification code for {username}: {code}")

# Helper: send password reset email
def send_password_reset_email(to_email, username, new_password):
    subject = "Walmart - Password Reset"
    message = f"""
    Hello {username},
    
    Your password has been reset successfully.
    
    New Password: {new_password}
    
    Please login with your new password and change it after your first login.
    
    Best regards,
    Walmart Security Team
    """
    
    # Try API first, fallback to console
    if not send_email_via_api(to_email, subject, message):
        print(f"PASSWORD RESET EMAIL: Sent to {to_email} - New password for {username}: {new_password}")

# Helper: generate random 6-digit code
def generate_verification_code():
    return ''.join(random.choices(string.digits, k=6))

@app.route('/verify_email', methods=['GET', 'POST'])
def verify_email():
    if not session.get('pending_email_verification'):
        return redirect(url_for('login'))
    error = None
    if request.method == 'POST':
        code_input = request.form.get('email_code')
        expected_code = session.get('email_verification_code')
        if code_input == expected_code:
            # Email verified, proceed to dashboard
            session.pop('pending_email_verification', None)
            session.pop('email_verification_code', None)
            user_id = session.get('pending_user_id')
            user = User.query.get(user_id)
            if user:
                session['user_id'] = user.id
                session['is_admin'] = user.is_admin
                session['username'] = user.username
                session.pop('pending_user_id', None)
                if user.is_admin:
                    return redirect(url_for('admin_dashboard'))
                else:
                    return redirect(url_for('employee_dashboard'))
        else:
            error = 'Invalid verification code.'
    return render_template('verify_email.html', error=error)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        # Check if form fields exist
        if 'username' not in request.form or 'password' not in request.form:
            error = 'Please fill in all required fields.'
            return render_template('login.html', error=error)
        
        username = request.form['username']
        password = request.form['password']
        
        # Check if username and password are not empty
        if not username or not password:
            error = 'Please fill in all required fields.'
            return render_template('login.html', error=error)
        
        user = User.query.filter_by(username=username).first()
        if not user or user.password != password:
            error = 'Invalid username or password.'
            return render_template('login.html', error=error)
        
        # Calculate trust score
        ip_address = request.remote_addr or request.headers.get('X-Forwarded-For', '127.0.0.1')
        latitude = None
        longitude = None
        try:
            # Use ipapi.co for better location detection
            geo_resp = requests.get(f'https://ipapi.co/{ip_address}/json/').json()
            if 'error' not in geo_resp:
                location = f"{geo_resp.get('city', 'Unknown')}, {geo_resp.get('country_name', 'Unknown')}"
                latitude = geo_resp.get('latitude')
                longitude = geo_resp.get('longitude')
            else:
                location = 'Unknown'
        except Exception:
            location = 'Unknown'
        
        prev = LoginAttempt.query.filter_by(user_id=user.id).order_by(LoginAttempt.timestamp.desc()).first()
        geo_distance = 0
        if prev and prev.latitude and prev.longitude and latitude and longitude:
            def haversine(lat1, lon1, lat2, lon2):
                R = 6371
                dlat = radians(lat2 - lat1)
                dlon = radians(lon2 - lon1)
                a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
                c = 2 * atan2(sqrt(a), sqrt(1-a))
                return R * c
            geo_distance = haversine(prev.latitude, prev.longitude, latitude, longitude)
        
        # Use timezone-aware datetime
        now = datetime.now(timezone.utc)
        api_rate = LoginAttempt.query.filter(LoginAttempt.user_id==user.id, LoginAttempt.timestamp>=now-timedelta(minutes=10)).count()
        failed_attempts = LoginAttempt.query.filter_by(user_id=user.id, is_suspicious=True).count()
        hour = now.hour
        
        trust_score, is_suspicious, require_passkey, new_location = ml_predict_trust_score(hour, geo_distance, failed_attempts, api_rate)
        
        # Store login attempt
        attempt = LoginAttempt(user_id=user.id, timestamp=now, ip_address=ip_address, location=location, latitude=latitude, longitude=longitude, trust_score=trust_score, is_suspicious=is_suspicious)
        db.session.add(attempt)
        db.session.commit()
        
        # Simplified trust score logic:
        # - Trust score < 50: Email verification required
        # - Trust score >= 50: Direct login
        
        if trust_score < 50:
            # Low trust - require email verification
            verification_code = generate_verification_code()
            session['pending_email_verification'] = True
            session['email_verification_code'] = verification_code
            session['pending_user_id'] = user.id
            send_verification_email(user.email, user.username, verification_code)
            return redirect(url_for('verify_email'))
        
        else:
            # High trust (>= 50) - direct login
            if is_suspicious:
                send_alert_email(user.email, user.username, 'Suspicious login attempt despite high trust score')
                error = 'Suspicious login detected. Access blocked and alert sent.'
                return render_template('login.html', error=error)
            
            # Success: set session and redirect
            session['user_id'] = user.id
            session['is_admin'] = user.is_admin
            session['username'] = user.username
            if user.is_admin:
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('employee_dashboard'))
    
    return render_template('login.html', error=error)

@app.route('/')
def index():
    if session.get('is_admin'):
        return redirect(url_for('admin_dashboard'))
    elif session.get('user_id'):
        return redirect(url_for('employee_dashboard'))
    else:
        return redirect(url_for('login'))

@app.route('/admin')
def admin_dashboard():
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    return render_template('admin.html')

@app.route('/employee')
def employee_dashboard():
    if not session.get('user_id') or session.get('is_admin'):
        return redirect(url_for('login'))
    # Fetch recent login attempts for this employee
    user_id = session['user_id']
    logs = LoginAttempt.query.filter_by(user_id=user_id).order_by(LoginAttempt.timestamp.desc()).limit(10).all()
    return render_template('employee.html', logs=logs, username=session.get('username'))

@app.route('/api/logs')
def api_logs():
    # Filter out admin logins, only show employee activities
    logs = db.session.query(LoginAttempt).join(User).filter(User.is_admin == False).order_by(LoginAttempt.timestamp.desc()).limit(100).all()
    data = []
    calcutta_tz = pytz.timezone('Asia/Calcutta')
    for log in logs:
        user = User.query.get(log.user_id)
        # Convert UTC to Calcutta time
        calcutta_time = log.timestamp.replace(tzinfo=pytz.UTC).astimezone(calcutta_tz)
        data.append({
            'id': log.id,
            'username': user.username if user else 'Unknown',
            'timestamp': calcutta_time.strftime('%Y-%m-%d %H:%M:%S'),
            'ip_address': log.ip_address,
            'location': log.location,
            'trust_score': log.trust_score,
            'is_suspicious': log.is_suspicious
        })
    return jsonify(data)

@app.route('/create_account', methods=['GET', 'POST'])
def create_account():
    error = None
    success = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            error = 'Username already exists.'
        elif User.query.filter_by(email=email).first():
            error = 'Email already registered.'
        else:
            # Create user without passkey
            user = User(username=username, password=password, email=email, is_admin=False, passkey="")
            db.session.add(user)
            db.session.commit()
            success = 'Account created successfully! You can now login.'
            # Redirect to login after 20 seconds
            return render_template('create_account.html', error=error, success=success, redirect=True, delay=20)
    return render_template('create_account.html', error=error, success=success)

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    error = None
    success = None
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        if user:
            # Generate new password
            new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
            user.password = new_password
            db.session.commit()
            # Send email
            send_password_reset_email(user.email, user.username, new_password)
            success = f'Password reset email sent to {email}'
            # Redirect to login after 3 seconds
            return render_template('forgot_password.html', error=error, success=success, redirect=True)
        else:
            error = 'Email not found.'
    return render_template('forgot_password.html', error=error, success=success)

@app.route('/delete_activity/<int:activity_id>', methods=['POST'])
def delete_activity(activity_id):
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    activity = LoginAttempt.query.get(activity_id)
    if activity:
        db.session.delete(activity)
        db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True) 