#!/bin/bash

# Walmart Employee Trust Score Application Runner

echo "🚀 Starting Walmart Employee Trust Score Application..."

# Set environment variables
export FLASK_APP=app_refactored.py
export FLASK_ENV=development
export SECRET_KEY="dev-secret-key-change-in-production"

# Set EmailJS credentials (replace with your actual values)
export EMAIL_SERVICE_ID="service_id"
export EMAIL_TEMPLATE_ID="template_id"
export EMAIL_USER_ID="user_id"

# Create necessary directories
mkdir -p logs templates static

# Install dependencies if needed
echo "📦 Checking dependencies..."
pip install Flask Flask-SQLAlchemy requests numpy joblib pytz python-dotenv

# Run the application
echo "🌐 Starting Flask application..."
echo "📍 Access the application at: http://localhost:5000"
echo "🛑 Press Ctrl+C to stop the application"
echo ""

python app_refactored.py 