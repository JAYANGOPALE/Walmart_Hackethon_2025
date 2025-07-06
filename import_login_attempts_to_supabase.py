import pandas as pd
from supabase import create_client, Client
import os
from datetime import datetime

# Load environment variables or hardcode your Supabase URL and Key
SUPABASE_URL = os.environ.get('SUPABASE_URL', "https://jhdxzuguiwexjranriru.supabase.co")
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpoZHh6dWd1aXdleGpyYW5yaXJ1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTA5NTI3MzEsImV4cCI6MjA2NjUyODczMX0.ukrNx7qiigAdKr4RZkhd7bFeKlTPqL5qLjUHg1ooaxY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Read the CSV
csv_file = 'employee_logins.csv'
df = pd.read_csv(csv_file)

for idx, row in df.iterrows():
    username = row['employee_name']
    # Lookup user_id by employee_name
    user_resp = supabase.table("users").select("id").eq("employee_name", username).execute()
    if not user_resp.data:
        print(f"User not found for username: {username}, skipping login attempt.")
        continue
    user_id = user_resp.data[0]['id']
    # Parse hour and minute from access_time
    try:
        hour, minute = map(int, str(row['access_time']).split(':'))
        timestamp = datetime(2024, 1, 1, hour, minute).isoformat()  # Use a fixed date for demo
    except Exception:
        timestamp = datetime.utcnow().isoformat()
    login_attempt = {
        "user_id": user_id,
        "timestamp": timestamp,
        "ip_address": "0.0.0.0",  # Placeholder, update if you have real IPs
        "location": "Unknown",    # Placeholder, update if you have real locations
        "latitude": None,
        "longitude": None,
        "trust_score": float(row['trust_score']),
        "is_suspicious": float(row['trust_score']) < 0.5,
        "failed_attempts": int(row['failed_attempts']),
        "geo_distance_km": float(row['geo_distance_km']),
        "api_rate": int(row['api_rate'])
    }
    response = supabase.table("login_attempts").insert(login_attempt).execute()
    if hasattr(response, 'data') and response.data:
        print(f"Inserted login attempt for user: {username}")
    else:
        print(f"Failed to insert login attempt for user: {username} - {getattr(response, 'error', 'Unknown error')}") 