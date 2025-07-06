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
import os
from supabase import create_client, Client
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///walmart.db'
db.init_app(app)
app.secret_key = 'supersecretkey'  # Needed for session

SUPABASE_URL = os.environ.get('SUPABASE_URL', "https://jhdxzuguiwexjranriru.supabase.co")
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpoZHh6dWd1aXdleGpyYW5yaXJ1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTA5NTI3MzEsImV4cCI6MjA2NjUyODczMX0.ukrNx7qiigAdKr4RZkhd7bFeKlTPqL5qLjUHg1ooaxY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Email API configuration
EMAIL_API_URL = "https://api.emailjs.com/api/v1.0/email/send"
EMAIL_SERVICE_ID = "service_id"  # Replace with your EmailJS service ID
EMAIL_TEMPLATE_ID = "template_id"  # Replace with your EmailJS template ID
EMAIL_USER_ID = "user_id"  # Replace with your EmailJS user ID

# SMTP Email configuration (Gmail)
SMTP_EMAIL = os.environ.get('SMTP_EMAIL', 'ishwarishinde2006@gmail.com')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', 'Pass@123')
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587

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

def send_email_smtp(to_email, subject, message):
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(message, 'plain'))
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.sendmail(SMTP_EMAIL, to_email, msg.as_string())
        server.quit()
        print(f"SMTP Email sent successfully to {to_email}")
        return True
    except Exception as e:
        print(f"SMTP Email sending failed: {e}")
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

# Helper: send password reset email (now uses SMTP)
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
    if not send_email_smtp(to_email, subject, message):
        print(f"PASSWORD RESET EMAIL: Sent to {to_email} - New password for {username}: {new_password}")

# Helper: generate random 6-digit code
def generate_verification_code():
    return ''.join(random.choices(string.digits, k=6))

def send_otp_email(to_email, username, otp):
    subject = "Walmart - Your Login OTP (Passkey)"
    message = f"""
    Hello {username},
    \nYour one-time passkey (OTP) for login is: {otp}\n\nThis code will expire in 5 minutes.\n\nIf you did not request this, please contact support.\n\nBest regards,\nWalmart Security Team
    """
    send_email_smtp(to_email, subject, message)

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
            user = supabase.table("users").select("*").eq("id", user_id).execute().data[0] if supabase.table("users").select("*").eq("id", user_id).execute().data else None
            if user:
                session['user_id'] = user['id']
                session['is_admin'] = user['is_admin']
                session['username'] = user['username']
                session.pop('pending_user_id', None)
                if user['is_admin']:
                    return redirect(url_for('admin_dashboard'))
                else:
                    return redirect(url_for('employee_dashboard'))
        else:
            error = 'Invalid verification code.'
    return render_template('verify_email.html', error=error)

def get_real_ip(request):
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr

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
        
        # Supabase user lookup
        user_resp = supabase.table("users").select("*").eq("username", username).execute()
        user = user_resp.data[0] if user_resp.data else None
        # Check hashed password
        if not user or not check_password_hash(user['password'], password):
            error = 'Invalid username or password.'
            return render_template('login.html', error=error)

        # Calculate trust score
        ip_address = get_real_ip(request)
        city = country = location = 'Unknown'
        latitude = longitude = None
        try:
            geo_resp = requests.get(f'https://ipapi.co/{ip_address}/json/').json()
            if 'error' not in geo_resp:
                city = geo_resp.get('city', 'Unknown')
                country = geo_resp.get('country_name', 'Unknown')
                location = f"{city}, {country}"
                latitude = geo_resp.get('latitude')
                longitude = geo_resp.get('longitude')
            else:
                print(f"Geo API error for IP {ip_address}: {geo_resp.get('reason', 'Unknown error')}")
        except Exception as e:
            print(f"Geo API exception for IP {ip_address}: {e}")
        
        # Supabase: get previous login attempts
        geo_distance = 0
        now = datetime.now(timezone.utc)
        api_rate = supabase.table("login_attempts").select("*").eq("user_id", user['id']).gte("timestamp", (now-timedelta(minutes=10)).isoformat()).execute().count
        failed_attempts = supabase.table("login_attempts").select("*").eq("user_id", user['id']).eq("is_suspicious", True).execute().count
        hour = now.hour
        trust_score, is_suspicious, require_passkey, new_location = ml_predict_trust_score(hour, geo_distance, failed_attempts, api_rate)
        # Supabase insert login attempt
        supabase.table("login_attempts").insert({
            "user_id": user['id'],
            "timestamp": now.isoformat(),
            "ip_address": ip_address,
            "location": location,
            "latitude": latitude,
            "longitude": longitude,
            "trust_score": trust_score,
            "is_suspicious": is_suspicious
        }).execute()
        
        # Trust score logic:
        if trust_score < 50:
            # Low trust - require email verification
            verification_code = generate_verification_code()
            session['pending_email_verification'] = True
            session['email_verification_code'] = verification_code
            session['pending_user_id'] = user['id']
            send_verification_email(user['email'], user['username'], verification_code)
            return redirect(url_for('verify_email'))
        else:
            # High trust (>= 50) - direct login
            if is_suspicious:
                send_alert_email(user['email'], user['username'], 'Suspicious login attempt despite high trust score')
                error = 'Suspicious login detected. Access blocked and alert sent.'
                return render_template('login.html', error=error)
            # Success: set session and redirect
            session['user_id'] = user['id']
            session['is_admin'] = user['is_admin']
            session['username'] = user['username']
            if user['is_admin']:
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('employee_dashboard'))
    return render_template('login.html', error=error)

@app.route('/verify_passkey', methods=['GET', 'POST'])
def verify_passkey():
    error = None
    if not session.get('pending_passkey_user_id'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        otp_input = request.form.get('passkey')
        otp_expected = session.get('pending_otp')
        otp_expiry = session.get('pending_otp_expiry')
        if not otp_expected or not otp_expiry or time.time() > otp_expiry:
            error = 'OTP expired. Please log in again.'
            session.pop('pending_passkey_user_id', None)
            session.pop('pending_is_admin', None)
            session.pop('pending_username', None)
            session.pop('pending_otp', None)
            session.pop('pending_otp_expiry', None)
            return render_template('verify_passkey.html', error=error, username=session.get('pending_username'))
        if otp_input == otp_expected:
            # OTP correct, log in
            user_id = session.get('pending_passkey_user_id')
            is_admin = session.get('pending_is_admin')
            username = session.get('pending_username')
            session['user_id'] = user_id
            session['is_admin'] = is_admin
            session['username'] = username
            session.pop('pending_passkey_user_id', None)
            session.pop('pending_is_admin', None)
            session.pop('pending_username', None)
            session.pop('pending_otp', None)
            session.pop('pending_otp_expiry', None)
            if is_admin:
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('employee_dashboard'))
        else:
            error = 'Invalid OTP. Please try again.'
    return render_template('verify_passkey.html', error=error, username=session.get('pending_username'))

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
    # SQLAlchemy render (no data fetch here, just template)
    return render_template('admin.html')

@app.route('/employee')
def employee_dashboard():
    if not session.get('user_id') or session.get('is_admin'):
        return redirect(url_for('login'))
    user_id = session['user_id']
    # Supabase fetch logs
    logs_resp = supabase.table("login_attempts").select("*").eq("user_id", user_id).order("timestamp", desc=True).limit(10).execute()
    logs = logs_resp.data if logs_resp.data else []
    return render_template('employee.html', logs=logs, username=session.get('username'))

@app.route('/api/logs')
def api_logs():
    # Supabase logs fetch (exclude admin users)
    users_resp = supabase.table("users").select("id,username").eq("is_admin", False).execute()
    user_ids = [u['id'] for u in users_resp.data] if users_resp.data else []
    logs = []
    if user_ids:
        logs_resp = supabase.table("login_attempts").select("*").in_("user_id", user_ids).order("timestamp", desc=True).limit(100).execute()
        logs = logs_resp.data if logs_resp.data else []
        # Attach username to each log
        user_map = {u['id']: u['username'] for u in users_resp.data}
        for log in logs:
            log['username'] = user_map.get(log['user_id'], 'Unknown')
    # Convert UTC to Calcutta time
    calcutta_tz = pytz.timezone('Asia/Calcutta')
    for log in logs:
        try:
            from datetime import datetime
            utc_time = datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00'))
            calcutta_time = utc_time.astimezone(calcutta_tz)
            log['timestamp'] = calcutta_time.strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            pass
    return jsonify(logs)

@app.route('/create_account', methods=['GET', 'POST'])
def create_account():
    error = None
    success = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        # Supabase user existence check
        user_exists = supabase.table("users").select("*").eq("username", username).execute().data
        email_exists = supabase.table("users").select("*").eq("email", email).execute().data
        if user_exists:
            error = 'Username already exists.'
        elif email_exists:
            error = 'Email already registered.'
        else:
            # Fetch IP and location
            ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
            city = country = location = 'Unknown'
            latitude = longitude = None
            try:
                geo_resp = requests.get(f'https://ipapi.co/{ip_address}/json/').json()
                if 'error' not in geo_resp:
                    city = geo_resp.get('city', 'Unknown')
                    country = geo_resp.get('country_name', 'Unknown')
                    location = f"{city}, {country}"
                    latitude = geo_resp.get('latitude')
                    longitude = geo_resp.get('longitude')
            except Exception as e:
                print(f"Geo API exception for IP {ip_address}: {e}")
            # Set analytics fields
            failed_attempts = 0
            geo_distance_km = 0.0
            now = datetime.now(timezone.utc)
            access_time = now.strftime('%H:%M')
            api_rate = 0
            hour = now.hour
            # Use ML trust module to compute trust_score
            trust_score, is_suspicious, require_passkey, new_location = ml_predict_trust_score(hour, geo_distance_km, failed_attempts, api_rate)
            # Hash the password before storing
            hashed_password = generate_password_hash(password)
            # Supabase insert user with analytics fields
            supabase.table("users").insert({
                "username": username,
                "password": hashed_password,
                "email": email,
                "is_admin": False,
                "passkey": "",
                "failed_attempts": failed_attempts,
                "geo_distance_km": geo_distance_km,
                "access_time": access_time,
                "api_rate": api_rate,
                "trust_score": trust_score
            }).execute()
            success = 'Account created successfully! You can now login.'
            return render_template('create_account.html', error=error, success=success, redirect=True, delay=20)
    return render_template('create_account.html', error=error, success=success)

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    error = None
    success = None
    if request.method == 'POST':
        email = request.form['email']
        user = supabase.table("users").select("*").eq("email", email).execute().data[0] if supabase.table("users").select("*").eq("email", email).execute().data else None
        if user:
            # Generate new password
            new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
            supabase.table("users").update({
                "password": new_password
            }).eq("id", user['id']).execute()
            # Send email
            send_password_reset_email(user['email'], user['username'], new_password)
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
    activity = supabase.table("login_attempts").select("*").eq("id", activity_id).execute().data[0] if supabase.table("login_attempts").select("*").eq("id", activity_id).execute().data else None
    if activity:
        supabase.table("login_attempts").delete().eq("id", activity['id']).execute()
    return redirect(url_for('admin_dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)

# Update admin user in Supabase
supabase.table("users").update({"is_admin": True}).eq("username", "admin").execute() 