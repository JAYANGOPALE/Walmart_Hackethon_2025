import pandas as pd
from werkzeug.security import generate_password_hash
from supabase import create_client, Client
import os

# Load environment variables or hardcode your Supabase URL and Key
SUPABASE_URL = os.environ.get('SUPABASE_URL', "https://jhdxzuguiwexjranriru.supabase.co")
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpoZHh6dWd1aXdleGpyYW5yaXJ1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTA5NTI3MzEsImV4cCI6MjA2NjUyODczMX0.ukrNx7qiigAdKr4RZkhd7bFeKlTPqL5qLjUHg1ooaxY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Read the CSV
csv_file = 'employee_logins.csv'
df = pd.read_csv(csv_file)

# Insert users into Supabase with all analytics fields
for idx, row in df.iterrows():
    user_data = {
        "employee_id": row["employee_id"],
        "username": row["employee_name"],
        "email": row["email"],
        "password": generate_password_hash(str(row["password"])),
        "is_admin": False,
        "failed_attempts": int(row["failed_attempts"]),
        "geo_distance_km": float(row["geo_distance_km"]),
        "access_time": row["access_time"],
        "api_rate": int(row["api_rate"]),
        "trust_score": float(row["trust_score"])
    }
    response = supabase.table("users").insert(user_data).execute()
    if hasattr(response, 'data') and response.data:
        print(f"Inserted user: {user_data['username']} ({user_data['email']})")
    else:
        print(f"Failed to insert user: {user_data['username']} ({user_data['email']}) - {getattr(response, 'error', 'Unknown error')}") 