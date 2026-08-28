import os
import logging
from typing import Tuple, Dict, Any
import numpy as np

logger = logging.getLogger("anomaly_detector")

MODEL_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "ml", "models", "anomaly", "isolation_forest.joblib")
)


class AnomalyDetector:
    def __init__(self) -> None:
        self.model = None
        self._load_model()

    def _load_model(self) -> None:
        try:
            import joblib
            if os.path.exists(MODEL_PATH):
                self.model = joblib.load(MODEL_PATH)
                logger.info(f"Loaded Isolation Forest model from {MODEL_PATH}")
        except Exception as e:
            logger.warning(f"Could not load ML anomaly model from {MODEL_PATH}: {e}. Using deterministic heuristic.")

    def predict_anomaly(self, features: Dict[str, Any]) -> Tuple[float, bool]:
        """
        Features dict keys: temp, rpm, vibration, soc, battery_temp, flow
        Returns: (anomaly_score: float [0.0 - 1.0], is_anomaly: bool)
        """
        temp = float(features.get("temp", features.get("temperature", 78.0)))
        rpm = float(features.get("rpm", 1500.0))
        vibration = float(features.get("vibration", 2.5))
        soc = float(features.get("soc", 85.0))
        bat_temp = float(features.get("battery_temp", 22.0))
        flow = float(features.get("flow", features.get("flow_rate", 85.0)))

        vector = np.array([[temp, rpm, vibration, soc, bat_temp, flow]])

        if self.model is not None:
            try:
                # Decision function gives raw score (lower = more abnormal)
                raw_score = self.model.decision_function(vector)[0]
                # Normalize raw score roughly to [0, 1] anomaly severity
                anomaly_score = float(np.clip(1.0 - (raw_score + 0.5), 0.0, 1.0))
                is_anomaly = bool(anomaly_score > 0.65)
                return anomaly_score, is_anomaly
            except Exception as e:
                logger.warning(f"Model prediction error: {e}")

        # High-precision fallback scoring
        temp_delta = max(0.0, temp - 85.0) / 20.0
        vib_delta = max(0.0, vibration - 6.0) / 10.0
        heuristic_score = min(1.0, temp_delta * 0.6 + vib_delta * 0.4)
        return round(heuristic_score, 3), heuristic_score > 0.5


anomaly_detector = AnomalyDetector()
