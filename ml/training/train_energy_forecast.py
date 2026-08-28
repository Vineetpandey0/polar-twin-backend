import os
import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor

# Ensure output directory exists
output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models", "forecasting"))
os.makedirs(output_dir, exist_ok=True)

# Generate synthetic historical hourly Antarctic data
np.random.seed(42)
n_samples = 8760 # 1 year of hourly samples

hour_of_day = np.arange(n_samples) % 24
month_of_year = (np.arange(n_samples) // (24 * 30)) % 12 + 1

# Ambient Antarctic temperature (-40°C in winter, -15°C in summer)
seasonal_temp = -28.0 + 12.0 * np.cos(2 * np.pi * (month_of_year - 1) / 12)
ambient_temp = seasonal_temp + np.random.normal(0, 4.0, n_samples)
wind_speed = np.random.weibull(2.0, n_samples) * 20.0

# Base load target in kW (higher heating demand in deep winter and evening meal times)
base_load = (
    85.0
    + (0.8 * np.maximum(0, -ambient_temp - 20)) # Heating penalty
    + (15.0 * np.sin(np.pi * (hour_of_day - 6) / 12)) # Daily operational curve
    + np.random.normal(0, 3.5, n_samples)
)

X_train = np.column_stack([hour_of_day, month_of_year, ambient_temp, wind_speed])
y_train = base_load

# Train Random Forest Regressor
forecaster = RandomForestRegressor(
    n_estimators=100,
    max_depth=12,
    random_state=42,
    n_jobs=-1,
)
forecaster.fit(X_train, y_train)

# Save model artifact
model_path = os.path.join(output_dir, "energy_forecast.joblib")
joblib.dump(forecaster, model_path)
print(f"[SUCCESS] Energy Forecasting Random Forest model saved to: {model_path}")
