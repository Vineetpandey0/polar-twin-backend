import os
import logging
from typing import List, Dict, Any
from datetime import datetime, timezone, timedelta
import numpy as np

logger = logging.getLogger("energy_forecaster")

MODEL_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "ml", "models", "forecasting", "energy_forecast.joblib")
)


class EnergyForecaster:
    def __init__(self) -> None:
        self.model = None
        self._load_model()

    def _load_model(self) -> None:
        try:
            import joblib
            if os.path.exists(MODEL_PATH):
                self.model = joblib.load(MODEL_PATH)
                logger.info(f"Loaded Energy Forecasting ML model from {MODEL_PATH}")
        except Exception as e:
            logger.warning(f"Could not load ML forecasting model: {e}")

    def forecast_24h(self, station_id: str, ambient_temp: float = -25.0) -> List[Dict[str, Any]]:
        now = datetime.now(timezone.utc)
        current_hour = now.hour
        current_month = now.month

        forecasts = []
        for step in range(1, 25):
            target_time = now + timedelta(hours=step)
            h = target_time.hour
            m = target_time.month

            # Simulated ambient diurnal variation
            temp = ambient_temp + 3.0 * np.sin(np.pi * (h - 14) / 12)
            wind = 25.0 + 8.0 * np.cos(np.pi * (h - 8) / 12)

            predicted_load = 110.0
            if self.model is not None:
                try:
                    feat = np.array([[h, m, temp, wind]])
                    predicted_load = float(self.model.predict(feat)[0])
                except Exception:
                    pass

            if station_id == "bharati":
                predicted_load *= 1.22 # Bharati larger research station coefficient

            generation_target = predicted_load + 20.0 # Reserve margin for BESS charging

            forecasts.append({
                "hour_offset": step,
                "timestamp": target_time.strftime("%Y-%m-%dT%H:00:00Z"),
                "predicted_load_kw": round(predicted_load, 1),
                "generation_target_kw": round(generation_target, 1),
                "projected_temp_c": round(temp, 1),
                "solar_contribution_kw": round(max(0.0, 15.0 * np.sin(np.pi * (h - 6) / 12)), 1),
            })

        return forecasts


energy_forecaster = EnergyForecaster()
