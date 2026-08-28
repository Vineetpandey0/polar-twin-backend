import os
import joblib
import numpy as np
from sklearn.ensemble import IsolationForest

# Ensure output directory exists
output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models", "anomaly"))
os.makedirs(output_dir, exist_ok=True)

# Generate synthetic baseline telemetry (nominal operation in Antarctic conditions)
np.random.seed(42)
n_samples = 2000

# Features: [generator_temp, generator_rpm, generator_vibration, battery_soc, battery_temp, hvac_flow]
temps = np.random.normal(78.0, 3.0, n_samples)          # Normal 75-82 deg C
rpms = np.random.normal(1500.0, 15.0, n_samples)        # Normal 1485-1515 RPM
vibrations = np.random.exponential(2.5, n_samples)      # Normal 1.5-4.5 mm/s
socs = np.random.uniform(60.0, 95.0, n_samples)         # Normal 60-95% SOC
bat_temps = np.random.normal(22.0, 2.0, n_samples)      # Normal 20-25 deg C
hvac_flows = np.random.normal(85.0, 5.0, n_samples)     # Normal 80-90%

X_train = np.column_stack([temps, rpms, vibrations, socs, bat_temps, hvac_flows])

# Train Isolation Forest Model
model = IsolationForest(
    n_estimators=100,
    contamination=0.03,
    random_state=42,
    bootstrap=True,
)
model.fit(X_train)

# Save model artifact
model_path = os.path.join(output_dir, "isolation_forest.joblib")
joblib.dump(model, model_path)
print(f"[SUCCESS] Anomaly Detection Isolation Forest model saved to: {model_path}")
