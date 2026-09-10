"""
Energy Load Forecasting Model Training — PolarTwin
=====================================================

Trains a RandomForestRegressor on synthetic-but-physics-informed hourly
load data for an Antarctic station power system.

Key improvements over a naive synthetic generator:
    1. wind_speed actually affects the load (wind-chill increases heating
       demand) — previously it was generated but never used, so the model
       had a feature with zero real signal.
    2. hour_of_day and month_of_year are cyclically encoded (sin/cos)
       instead of raw integers, so the model understands that hour 23 is
       adjacent to hour 0, and December is adjacent to January.
    3. Lag features (load 1 hour ago, load 24 hours ago) are added, since
       real load forecasting benefits heavily from short-term
       autocorrelation, not just calendar + weather.
    4. A proper train/test split + MAE/RMSE/R^2 evaluation, so you have
       concrete accuracy numbers instead of just "it's trained".
"""

import os
import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models", "forecasting"))
os.makedirs(output_dir, exist_ok=True)

rng = np.random.default_rng(42)
n_samples = 8760  # 1 year of hourly samples

hour_of_day = np.arange(n_samples) % 24
month_of_year = (np.arange(n_samples) // (24 * 30)) % 12 + 1

# ---------------------------------------------------------------------------
# Weather generation
# ---------------------------------------------------------------------------
seasonal_temp = -28.0 + 12.0 * np.cos(2 * np.pi * (month_of_year - 1) / 12)
ambient_temp = seasonal_temp + rng.normal(0, 4.0, n_samples)
wind_speed = rng.weibull(2.0, n_samples) * 20.0  # km/h-ish scale

# ---------------------------------------------------------------------------
# Load generation (now wind-coupled)
# ---------------------------------------------------------------------------
# Wind chill approximation: wind strips heat faster at colder temps, so its
# effect on heating demand should scale with how cold it already is.
cold_severity = np.maximum(0, -ambient_temp - 20)  # 0 once above -20C
wind_chill_penalty = 0.15 * wind_speed * (cold_severity / 20.0)

base_load = (
    85.0
    + 0.8 * cold_severity                              # heating penalty
    + wind_chill_penalty                                # wind makes cold worse
    + 15.0 * np.sin(np.pi * (hour_of_day - 6) / 12)     # daily operational curve
    + rng.normal(0, 3.5, n_samples)
)

# ---------------------------------------------------------------------------
# Feature engineering
# ---------------------------------------------------------------------------
# Cyclical encoding so hour 23 / hour 0 and month 12 / month 1 are "close"
hour_sin = np.sin(2 * np.pi * hour_of_day / 24)
hour_cos = np.cos(2 * np.pi * hour_of_day / 24)
month_sin = np.sin(2 * np.pi * (month_of_year - 1) / 12)
month_cos = np.cos(2 * np.pi * (month_of_year - 1) / 12)

# Lag features: load 1 hour ago and 24 hours ago (autoregressive signal).
# For the first 24 samples there's no real history, so we backfill with the
# same value (a real deployment would just drop these rows or start the
# lookback later; keeping them here so array shapes line up simply).
load_lag_1h = np.roll(base_load, 1)
load_lag_1h[0] = base_load[0]
load_lag_24h = np.roll(base_load, 24)
load_lag_24h[:24] = base_load[:24]

FEATURE_NAMES = [
    "hour_sin", "hour_cos", "month_sin", "month_cos",
    "ambient_temp", "wind_speed", "load_lag_1h", "load_lag_24h",
]

X = np.column_stack([
    hour_sin, hour_cos, month_sin, month_cos,
    ambient_temp, wind_speed, load_lag_1h, load_lag_24h,
])
y = base_load

# ---------------------------------------------------------------------------
# Train/test split (chronological — no shuffling, since this is time series
# and shuffling would leak future information into training via lag features)
# ---------------------------------------------------------------------------
split_idx = int(n_samples * 0.8)
X_train, X_test = X[:split_idx], X[split_idx:]
y_train, y_test = y[:split_idx], y[split_idx:]

# ---------------------------------------------------------------------------
# Train Random Forest Regressor
# ---------------------------------------------------------------------------
forecaster = RandomForestRegressor(
    n_estimators=200,
    max_depth=12,
    random_state=42,
    n_jobs=-1,
)
forecaster.fit(X_train, y_train)

# ---------------------------------------------------------------------------
# Evaluate on held-out (future, unseen) data
# ---------------------------------------------------------------------------
y_pred = forecaster.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
r2 = r2_score(y_test, y_pred)

print("\n=== Evaluation (held-out final 20% of the year) ===")
print(f"MAE:  {mae:.2f} kW")
print(f"RMSE: {rmse:.2f} kW")
print(f"R^2:  {r2:.3f}")

print("\n=== Feature importances ===")
for name, importance in sorted(zip(FEATURE_NAMES, forecaster.feature_importances_),
                                key=lambda t: -t[1]):
    print(f"  {name:15s} {importance:.3f}")

# ---------------------------------------------------------------------------
# Refit on full dataset for the final deployed model
# (common practice: evaluate on a split, then use all available data for
# the artifact you actually ship)
# ---------------------------------------------------------------------------
forecaster.fit(X, y)

# ---------------------------------------------------------------------------
# Save model artifact + metadata
# ---------------------------------------------------------------------------
model_path = os.path.join(output_dir, "energy_forecast.joblib")
joblib.dump(forecaster, model_path)

metadata = {
    "feature_names": FEATURE_NAMES,
    "feature_notes": {
        "hour_sin/hour_cos": "cyclical encoding of hour_of_day (0-23)",
        "month_sin/month_cos": "cyclical encoding of month_of_year (1-12)",
        "load_lag_1h": "predicted/actual load from 1 hour prior (kW)",
        "load_lag_24h": "predicted/actual load from 24 hours prior (kW)",
    },
    "target": "base_load (kW)",
    "eval_mae_kw": round(float(mae), 2),
    "eval_rmse_kw": round(float(rmse), 2),
    "eval_r2": round(float(r2), 3),
    "trained_on": "physics-informed synthetic hourly telemetry (n=%d)" % n_samples,
}
metadata_path = os.path.join(output_dir, "energy_forecast_metadata.joblib")
joblib.dump(metadata, metadata_path)

print(f"\n[SUCCESS] Energy Forecasting Random Forest model saved to: {model_path}")
print(f"[SUCCESS] Metadata saved to: {metadata_path}")