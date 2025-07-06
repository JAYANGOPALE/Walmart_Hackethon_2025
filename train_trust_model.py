import pandas as pd
from sklearn.ensemble import IsolationForest
from joblib import dump

# Load real employee login data
# The CSV should be named 'employee_logins.csv' and placed in the project root
# Columns: employee_id,employee_name,failed_attempts,geo_distance_km,access_time,api_rate,trust_score
df = pd.read_csv('employee_logins.csv')

# Parse hour from access_time (format: HH:MM)
df['hour'] = df['access_time'].str.split(':').str[0].astype(int)

# Select features for training
X = df[['hour', 'geo_distance_km', 'failed_attempts', 'api_rate']].values

# Train Isolation Forest
model = IsolationForest(contamination=0.05, random_state=42)
model.fit(X)

dump(model, 'trust_model.joblib')
print('Isolation Forest model trained and saved as trust_model.joblib') 