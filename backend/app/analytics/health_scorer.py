from typing import Dict, Any, Tuple
from app.analytics.anomaly_detector import anomaly_detector


class HealthScorer:
    def score_asset(self, asset_state: Dict[str, Any]) -> Tuple[float, float, float]:
        """
        Calculates:
        - health_score: 0.0 - 1.0
        - failure_probability: 0.0 - 1.0
        - rul_hours (Remaining Useful Life): in hours
        """
        readings = asset_state.get("sensor_readings", {})
        status = asset_state.get("operational_status", "RUNNING")

        # 1. Base status penalty
        if status == "FAILED":
            return 0.15, 0.95, 0.0
        elif status == "WARNING":
            base_health = 0.70
        else:
            base_health = 0.98

        # 2. ML Anomaly Score
        anomaly_score, is_anomaly = anomaly_detector.predict_anomaly(readings)

        # 3. Penalties
        temp = float(readings.get("temperature", readings.get("temp", 78.0)))
        temp_penalty = max(0.0, temp - 82.0) * 0.02

        vibration = float(readings.get("vibration", 2.0))
        vib_penalty = max(0.0, vibration - 4.5) * 0.04

        soc = float(readings.get("soc", 90.0))
        soc_penalty = max(0.0, 30.0 - soc) * 0.01 if asset_state.get("asset_type") == "BATTERY" else 0.0

        # Weighted Health Calculation
        total_penalty = (anomaly_score * 0.35) + temp_penalty + vib_penalty + soc_penalty
        health_score = round(float(max(0.10, min(1.0, base_health - total_penalty))), 3)

        # Failure Probability (Sigmoid-like inverse of health)
        failure_prob = round(float(max(0.01, min(0.99, (1.0 - health_score) * 1.2))), 3)

        # Remaining Useful Life (RUL) estimation
        if health_score >= 0.90:
            rul_hours = 8500.0 * (health_score / 0.95)
        elif health_score >= 0.75:
            rul_hours = 2400.0 * (health_score / 0.85)
        else:
            rul_hours = 320.0 * (health_score / 0.50)

        return health_score, failure_prob, round(rul_hours, 1)


health_scorer = HealthScorer()
