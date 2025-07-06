import pandas as pd
import matplotlib.pyplot as plt
from joblib import load

# Load your data and model
csv_file = 'employee_logins.csv'
model_file = 'trust_model.joblib'
df = pd.read_csv(csv_file)
model = load(model_file)

# Prepare features
# Parse hour from access_time (format: HH:MM)
df['hour'] = df['access_time'].str.split(':').str[0].astype(int)
X = df[['hour', 'geo_distance_km', 'failed_attempts', 'api_rate']].values

# Get anomaly scores and predictions
anomaly_scores = model.decision_function(X)
predictions = model.predict(X)  # -1: anomaly, 1: normal

# Add to DataFrame
df['anomaly_score'] = anomaly_scores
df['is_anomaly'] = predictions == -1

# Plot anomaly score distribution
plt.figure(figsize=(12,6))
plt.hist(anomaly_scores, bins=30, color='skyblue', edgecolor='black')
plt.title('Anomaly Score Distribution')
plt.xlabel('Anomaly Score')
plt.ylabel('Frequency')
plt.tight_layout()
plt.show()

# Highlight anomalies in a scatter plot
plt.figure(figsize=(12,6))
colors = df['is_anomaly'].map({True: 'red', False: 'green'})
plt.scatter(df.index, anomaly_scores, c=colors, label='Anomaly', alpha=0.7)
plt.title('Anomaly Scores by Login')
plt.xlabel('Login Index')
plt.ylabel('Anomaly Score')
plt.legend(['Normal', 'Anomaly'])
plt.tight_layout()
plt.show()

# Print summary
print(f"Total logins: {len(df)}")
print(f"Anomalies detected: {df['is_anomaly'].sum()}") 