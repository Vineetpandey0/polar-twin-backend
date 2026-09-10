"""
Anomaly Detection Model Training — PolarTwin
==============================================

Trains an IsolationForest on synthetic-but-physics-informed telemetry
for an Antarctic station power/HVAC system.

Key improvement over a naive synthetic generator:
    Instead of sampling each feature independently (which teaches the
    model nothing about how a real generator/battery/HVAC system
    behaves), features here are causally coupled:
        - generator_rpm droops as generator_temp rises above setpoint
        - generator_vibration scales with |rpm - setpoint| (mechanical
          stress), not pure noise
        - battery_temp responds to charge/discharge rate (dSOC/dt) and
          ambient/HVAC conditions
        - hvac_flow compensates for ambient cold + battery thermal load

This means the IsolationForest actually learns *relationships* between
sensors, so it can catch anomalies where a single sensor looks "in range"
but its relationship to the others is broken (the realistic failure mode).

We also generate a labeled fault-scenario set (held out, never trained on)
so you can demonstrate/quantify detection performance in a hackathon demo
instead of just asserting "it works".
"""

import os
import joblib
import numpy as np
from sklearn.ensemble import IsolationForest

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models", "anomaly"))
os.makedirs(output_dir, exist_ok=True)

rng = np.random.default_rng(42)

FEATURE_NAMES = [
    "generator_temp",      # deg C
    "generator_rpm",       # RPM
    "generator_vibration", # mm/s
    "battery_soc",         # %
    "battery_temp",        # deg C
    "hvac_flow",           # %
]

# Setpoints / nominal operating targets
GEN_TEMP_SETPOINT = 78.0     # deg C
GEN_RPM_SETPOINT = 1500.0    # RPM
AMBIENT_TEMP_RANGE = (-45.0, -15.0)  # deg C, realistic Antarctic winter/summer range


# ---------------------------------------------------------------------------
# Physics-informed nominal telemetry generator
# ---------------------------------------------------------------------------
def generate_nominal_telemetry(n_samples: int, seed_rng: np.random.Generator) -> np.ndarray:
    """
    Generate correlated, physically plausible NOMINAL operating telemetry.
    """
    # Simulated ambient outdoor temperature drives HVAC/battery thermal load
    ambient_temp = seed_rng.uniform(*AMBIENT_TEMP_RANGE, n_samples)

    # Generator load fraction (0.4-1.0) drives temp/rpm/vibration together
    load_frac = seed_rng.uniform(0.4, 1.0, n_samples)

    # Generator temp rises with load, small measurement noise
    generator_temp = GEN_TEMP_SETPOINT + (load_frac - 0.7) * 12.0 + seed_rng.normal(0, 1.2, n_samples)

    # RPM droops slightly as temp rises above setpoint (governor compensation lag)
    rpm_droop = np.clip(generator_temp - GEN_TEMP_SETPOINT, 0, None) * 1.8
    generator_rpm = GEN_RPM_SETPOINT - rpm_droop + seed_rng.normal(0, 4.0, n_samples)

    # Vibration scales with mechanical stress (rpm deviation from setpoint) + load
    rpm_dev = np.abs(generator_rpm - GEN_RPM_SETPOINT)
    generator_vibration = 1.2 + 0.15 * rpm_dev + 1.5 * load_frac + seed_rng.exponential(0.6, n_samples)

    # Battery SOC: slow random walk within operating band (charge/discharge cycles)
    battery_soc = np.clip(seed_rng.uniform(55.0, 95.0, n_samples), 0, 100)

    # dSOC/dt proxy: higher load -> more discharge -> more battery heat
    discharge_rate = load_frac  # proxy for how hard the battery is working
    # Battery temp: baseline responds to ambient (poorly insulated packs run cold
    # in extreme ambient) and heats up under high discharge rate
    battery_temp = (22.0
                     + 0.06 * (ambient_temp - (-30.0))   # ambient coupling
                     + 3.0 * (discharge_rate - 0.7)       # self-heating under load
                     + seed_rng.normal(0, 1.0, n_samples))

    # HVAC flow compensates for cold ambient + battery thermal regulation needs
    hvac_flow = np.clip(
        70.0
        - 0.5 * (ambient_temp - (-30.0))   # colder ambient -> HVAC works harder
        + 2.0 * np.abs(battery_temp - 22.0)  # extra flow to regulate battery temp
        + seed_rng.normal(0, 3.0, n_samples),
        0, 100,
    )

    return np.column_stack([
        generator_temp, generator_rpm, generator_vibration,
        battery_soc, battery_temp, hvac_flow,
    ])


# ---------------------------------------------------------------------------
# Labeled fault scenario generator (for evaluation only — never trained on)
# ---------------------------------------------------------------------------
def generate_fault_scenarios(n_per_fault: int, seed_rng: np.random.Generator):
    """
    Generate realistic, correlated FAULT telemetry for evaluation.
    Returns (X_faults, labels) where labels describe the fault type.
    """
    faults = []
    labels = []

    # --- Fault 1: Generator overheat cascade ---
    # Temp climbs well above setpoint -> RPM droops hard -> vibration spikes
    load_frac = seed_rng.uniform(0.9, 1.0, n_per_fault)
    generator_temp = GEN_TEMP_SETPOINT + seed_rng.uniform(15, 30, n_per_fault)
    rpm_droop = (generator_temp - GEN_TEMP_SETPOINT) * 2.5
    generator_rpm = GEN_RPM_SETPOINT - rpm_droop + seed_rng.normal(0, 5, n_per_fault)
    rpm_dev = np.abs(generator_rpm - GEN_RPM_SETPOINT)
    generator_vibration = 1.2 + 0.3 * rpm_dev + seed_rng.exponential(1.5, n_per_fault)
    battery_soc = seed_rng.uniform(55, 95, n_per_fault)
    battery_temp = seed_rng.normal(23, 1.5, n_per_fault)
    hvac_flow = seed_rng.uniform(75, 90, n_per_fault)
    faults.append(np.column_stack([generator_temp, generator_rpm, generator_vibration,
                                    battery_soc, battery_temp, hvac_flow]))
    labels += ["generator_overheat_cascade"] * n_per_fault

    # --- Fault 2: Battery thermal runaway precursor ---
    # Battery temp rises sharply despite normal/low discharge (decoupled from load)
    generator_temp = seed_rng.normal(78, 3, n_per_fault)
    generator_rpm = seed_rng.normal(1500, 15, n_per_fault)
    generator_vibration = seed_rng.exponential(2.0, n_per_fault)
    battery_soc = seed_rng.uniform(60, 90, n_per_fault)
    battery_temp = seed_rng.uniform(35, 50, n_per_fault)  # abnormally hot, unlinked to load
    hvac_flow = seed_rng.uniform(80, 90, n_per_fault)      # HVAC hasn't compensated yet
    faults.append(np.column_stack([generator_temp, generator_rpm, generator_vibration,
                                    battery_soc, battery_temp, hvac_flow]))
    labels += ["battery_thermal_runaway_precursor"] * n_per_fault

    # --- Fault 3: HVAC failure during extreme cold snap ---
    # Ambient effectively very cold, HVAC flow collapses -> battery temp drops out of band
    generator_temp = seed_rng.normal(78, 3, n_per_fault)
    generator_rpm = seed_rng.normal(1500, 15, n_per_fault)
    generator_vibration = seed_rng.exponential(2.0, n_per_fault)
    battery_soc = seed_rng.uniform(55, 90, n_per_fault)
    hvac_flow = seed_rng.uniform(5, 25, n_per_fault)   # HVAC failed/degraded
    battery_temp = seed_rng.uniform(-5, 8, n_per_fault)  # cold-soaked, out of nominal band
    faults.append(np.column_stack([generator_temp, generator_rpm, generator_vibration,
                                    battery_soc, battery_temp, hvac_flow]))
    labels += ["hvac_failure_cold_snap"] * n_per_fault

    # --- Fault 4: Slow sensor drift (stuck/miscalibrated vibration sensor) ---
    # Vibration reads implausibly flat/low regardless of load - decoupled from rpm
    load_frac = seed_rng.uniform(0.4, 1.0, n_per_fault)
    generator_temp = GEN_TEMP_SETPOINT + (load_frac - 0.7) * 12.0 + seed_rng.normal(0, 1.2, n_per_fault)
    generator_rpm = seed_rng.normal(1500, 15, n_per_fault)
    generator_vibration = seed_rng.uniform(0.05, 0.2, n_per_fault)  # implausibly flat -> stuck sensor
    battery_soc = seed_rng.uniform(55, 95, n_per_fault)
    battery_temp = seed_rng.normal(22, 2, n_per_fault)
    hvac_flow = seed_rng.normal(85, 5, n_per_fault)
    faults.append(np.column_stack([generator_temp, generator_rpm, generator_vibration,
                                    battery_soc, battery_temp, hvac_flow]))
    labels += ["stuck_vibration_sensor"] * n_per_fault

    return np.vstack(faults), np.array(labels)


# ---------------------------------------------------------------------------
# Generate data
# ---------------------------------------------------------------------------
N_TRAIN = 4000
X_train = generate_nominal_telemetry(N_TRAIN, rng)

N_PER_FAULT = 150
X_faults, fault_labels = generate_fault_scenarios(N_PER_FAULT, rng)

# Small nominal holdout to check false-positive rate on data the model
# hasn't literally memorized (still drawn from the nominal generator).
N_HOLDOUT = 500
X_holdout_nominal = generate_nominal_telemetry(N_HOLDOUT, rng)

# ---------------------------------------------------------------------------
# Train Isolation Forest
# ---------------------------------------------------------------------------
model = IsolationForest(
    n_estimators=200,
    contamination=0.03,
    max_samples="auto",
    random_state=42,
    bootstrap=True,
)
model.fit(X_train)

# ---------------------------------------------------------------------------
# Evaluate on held-out nominal data + labeled fault scenarios
# ---------------------------------------------------------------------------
def summarize(name, X, expect_anomaly: bool):
    preds = model.predict(X)  # 1 = normal, -1 = anomaly
    scores = model.decision_function(X)  # higher = more normal
    anomaly_rate = np.mean(preds == -1)
    print(f"[{name}] n={len(X)}  flagged_anomaly_rate={anomaly_rate:.1%}  "
          f"mean_score={scores.mean():.3f}  "
          f"({'expected high' if expect_anomaly else 'expected low'})")
    return anomaly_rate

print("\n=== Evaluation ===")
summarize("Held-out nominal", X_holdout_nominal, expect_anomaly=False)

for fault_type in np.unique(fault_labels):
    mask = fault_labels == fault_type
    summarize(fault_type, X_faults[mask], expect_anomaly=True)

# ---------------------------------------------------------------------------
# Save model artifact + metadata
# ---------------------------------------------------------------------------
model_path = os.path.join(output_dir, "isolation_forest.joblib")
joblib.dump(model, model_path)

metadata = {
    "feature_names": FEATURE_NAMES,
    "gen_temp_setpoint": GEN_TEMP_SETPOINT,
    "gen_rpm_setpoint": GEN_RPM_SETPOINT,
    "trained_on": "physics-informed synthetic nominal telemetry (n=%d)" % N_TRAIN,
    "fault_scenarios_evaluated": sorted(np.unique(fault_labels).tolist()),
}
metadata_path = os.path.join(output_dir, "isolation_forest_metadata.joblib")
joblib.dump(metadata, metadata_path)

print(f"\n[SUCCESS] Anomaly Detection Isolation Forest model saved to: {model_path}")
print(f"[SUCCESS] Metadata saved to: {metadata_path}")